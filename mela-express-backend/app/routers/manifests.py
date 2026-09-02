from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, func
from sqlalchemy.orm import selectinload
from typing import Optional
import uuid

from app.database import get_db
from app.models import (
    TransferManifest, ManifestParcel, Parcel, ManifestStatus, ParcelStatus,
    StaffRole, ManifestCheckpoint, Branch, PaymentMode, PaymentStatus,
)
from app.schemas import (
    ManifestCreate, ManifestOut, ManifestDetailOut, ManifestReceive,
    ParcelOut, ManifestCheckpointCreate, ManifestCheckpointOut, ParcelScanRequest, ParcelScanOut,
)
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.exceptions import NotFoundError, PaymentRequired
from app.core.pagination import paginate
from app.core.scan_workflow import normalize_scan_code, resolve_scan, ScanFailure
from app.core.state_machine import validate_transition, InvalidTransition, payment_gated
from app.services.journey import load_parcel_for_update, notify_after_scan, record_scan
from app.services.labels import track_url
from app.i18n import t as i18n_t

router = APIRouter(prefix="/api/manifests", tags=["manifests"])


async def _manifest_out(db: AsyncSession, manifest: TransferManifest, parcel_count: int | None = None) -> ManifestOut:
    if parcel_count is None:
        parcel_count = await db.scalar(
            select(func.count()).select_from(ManifestParcel).where(ManifestParcel.manifest_id == manifest.id)
        ) or 0
    return ManifestOut(
        id=manifest.id,
        origin_branch_id=manifest.origin_branch_id,
        destination_branch_id=manifest.destination_branch_id,
        status=manifest.status,
        driver_name=manifest.driver_name,
        vehicle_plate=manifest.vehicle_plate,
        notes=manifest.notes,
        created_at=manifest.created_at,
        parcel_count=parcel_count,
    )


@router.post("", response_model=ManifestOut)
async def create_manifest(
    manifest_in: ManifestCreate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    manifest = TransferManifest(
        origin_branch_id=manifest_in.origin_branch_id,
        destination_branch_id=manifest_in.destination_branch_id,
        driver_name=manifest_in.driver_name,
        vehicle_plate=manifest_in.vehicle_plate,
        notes=manifest_in.notes,
        created_by=current_user.id,
        status=ManifestStatus.IN_TRANSIT,
    )
    db.add(manifest)
    await db.flush()

    origin = await db.get(Branch, manifest_in.origin_branch_id)
    count = 0
    for parcel_id in manifest_in.parcel_ids:
        parcel = await load_parcel_for_update(db, parcel_id)
        if not parcel:
            continue
        try:
            validate_transition(parcel.status, ParcelStatus.IN_TRANSIT)
        except InvalidTransition:
            continue
        if parcel.payment_mode == PaymentMode.BEFORE and parcel.payment_status != PaymentStatus.PAID:
            if payment_gated(ParcelStatus.IN_TRANSIT):
                continue
        await record_scan(
            db,
            parcel,
            to_status=ParcelStatus.IN_TRANSIT,
            staff_id=current_user.id,
            branch_id=manifest_in.origin_branch_id,
            note=f"Loaded on manifest {manifest.id} — {manifest_in.vehicle_plate or 'vehicle TBD'}",
            location_name=origin.name if origin else None,
            source="manifest",
        )
        db.add(ManifestParcel(manifest_id=manifest.id, parcel_id=parcel.id))
        count += 1

    await db.commit()
    await db.refresh(manifest)
    return await _manifest_out(db, manifest, count)


@router.get("", response_model=dict)
async def list_manifests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(TransferManifest)
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        query = query.where(
            or_(
                TransferManifest.origin_branch_id == current_user.branch_id,
                TransferManifest.destination_branch_id == current_user.branch_id,
            )
        )
    query = query.order_by(desc(TransferManifest.created_at))
    items, total = await paginate(query, db, page=page, size=size)
    manifest_list = [await _manifest_out(db, m) for m in items]
    pages = (total + size - 1) // size if total > 0 else 0
    return {"items": manifest_list, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/{manifest_id}", response_model=ManifestDetailOut)
async def get_manifest(
    manifest_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    manifest = await db.get(TransferManifest, manifest_id)
    if not manifest:
        raise NotFoundError("Manifest not found")

    mps = (await db.execute(select(ManifestParcel).where(ManifestParcel.manifest_id == manifest.id))).scalars().all()
    parcels = []
    for mp in mps:
        p = await db.get(Parcel, mp.parcel_id)
        if p:
            parcels.append(ParcelOut.model_validate(p))

    cps = (
        await db.execute(
            select(ManifestCheckpoint)
            .where(ManifestCheckpoint.manifest_id == manifest.id)
            .order_by(ManifestCheckpoint.created_at.desc())
        )
    ).scalars().all()

    return ManifestDetailOut(
        id=manifest.id,
        origin_branch_id=manifest.origin_branch_id,
        destination_branch_id=manifest.destination_branch_id,
        status=manifest.status,
        driver_name=manifest.driver_name,
        vehicle_plate=manifest.vehicle_plate,
        notes=manifest.notes,
        created_at=manifest.created_at,
        parcel_count=len(parcels),
        parcels=parcels,
        checkpoints=[ManifestCheckpointOut.model_validate(cp) for cp in cps],
    )


@router.post("/{manifest_id}/checkpoints", response_model=ManifestCheckpointOut)
async def add_manifest_checkpoint(
    manifest_id: uuid.UUID,
    checkpoint_in: ManifestCheckpointCreate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.DRIVER, StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    manifest = await db.get(TransferManifest, manifest_id)
    if not manifest:
        raise NotFoundError("Manifest not found")
    cp = ManifestCheckpoint(
        manifest_id=manifest.id,
        location_name=checkpoint_in.location_name,
        latitude=checkpoint_in.latitude,
        longitude=checkpoint_in.longitude,
        note=checkpoint_in.note,
        created_by=current_user.id,
    )
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp


@router.post("/{manifest_id}/scan", response_model=ParcelScanOut)
async def scan_manifest_parcel(
    manifest_id: uuid.UUID,
    body: ParcelScanRequest,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.DRIVER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Scan a parcel sticker while receiving a manifest — auto-advances status."""
    manifest = await db.get(TransferManifest, manifest_id)
    if not manifest:
        raise NotFoundError("Manifest not found")

    code = normalize_scan_code(body.code)
    parcel = (await db.execute(select(Parcel).where(Parcel.tracking_code == code))).scalar_one_or_none()
    if not parcel:
        raise NotFoundError(f"No parcel found for {code}")

    mp = (
        await db.execute(
            select(ManifestParcel).where(
                ManifestParcel.manifest_id == manifest.id,
                ManifestParcel.parcel_id == parcel.id,
            )
        )
    ).scalar_one_or_none()
    if not mp:
        raise HTTPException(status_code=409, detail="Parcel is not on this manifest.")

    branch = await db.get(Branch, current_user.branch_id) if current_user.branch_id else None
    if branch is None:
        branch = await db.get(Branch, manifest.destination_branch_id)

    resolution = resolve_scan(parcel, branch, role=current_user.role)
    if isinstance(resolution, ScanFailure):
        raise HTTPException(status_code=409, detail=resolution.message)

    parcel = await load_parcel_for_update(db, parcel.id)
    from_status = parcel.status
    await record_scan(
        db,
        parcel,
        to_status=resolution.to_status,
        staff_id=current_user.id,
        branch_id=branch.id if branch else manifest.destination_branch_id,
        note=body.note or f"Manifest receive scan — {resolution.note}",
        location_name=resolution.station_label,
        source="manifest_scan",
    )
    mp.received = True
    mp.received_by = current_user.id
    await db.commit()
    await notify_after_scan(db, parcel, resolution.to_status, body.note)

    return ParcelScanOut(
        tracking_code=parcel.tracking_code,
        from_status=from_status,
        to_status=resolution.to_status,
        status_label=i18n_t(f"parcel_status.{resolution.to_status.value}"),
        station=resolution.station_label,
        message=f"Received on manifest — {i18n_t(f'parcel_status.{resolution.to_status.value}')}",
        track_url=track_url(parcel.tracking_code),
    )


@router.post("/{manifest_id}/receive", response_model=ManifestOut)
async def receive_manifest(
    manifest_id: uuid.UUID,
    payload: ManifestReceive,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    manifest = await db.get(TransferManifest, manifest_id)
    if not manifest:
        raise NotFoundError("Manifest not found")

    dest = await db.get(Branch, manifest.destination_branch_id)
    mps = (await db.execute(select(ManifestParcel).where(ManifestParcel.manifest_id == manifest.id))).scalars().all()

    for mp in mps:
        parcel = await load_parcel_for_update(db, mp.parcel_id)
        if not parcel:
            continue
        if mp.parcel_id in payload.received_parcel_ids:
            mp.received = True
            mp.received_by = current_user.id
            target = ParcelStatus.ARRIVED_AT_DESTINATION
            try:
                validate_transition(parcel.status, target)
                await record_scan(
                    db,
                    parcel,
                    to_status=target,
                    staff_id=current_user.id,
                    branch_id=manifest.destination_branch_id,
                    note="Manifest received at destination",
                    location_name=dest.name if dest else None,
                    source="manifest",
                )
            except InvalidTransition:
                pass
        elif not mp.received:
            try:
                validate_transition(parcel.status, ParcelStatus.ON_HOLD)
                await record_scan(
                    db,
                    parcel,
                    to_status=ParcelStatus.ON_HOLD,
                    staff_id=current_user.id,
                    branch_id=manifest.destination_branch_id,
                    note="Missing from manifest receive — on hold",
                    location_name=dest.name if dest else None,
                    source="manifest",
                )
            except InvalidTransition:
                pass

    manifest.status = ManifestStatus.RECEIVED
    await db.commit()
    await db.refresh(manifest)
    return await _manifest_out(db, manifest, len(mps))
