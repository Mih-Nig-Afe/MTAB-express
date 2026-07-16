from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, func
from sqlalchemy.orm import selectinload
from typing import Optional
import uuid

from app.database import get_db
from app.models import TransferManifest, ManifestParcel, Parcel, ManifestStatus, ParcelStatus, StaffRole
from app.schemas import ManifestCreate, ManifestOut, ManifestDetailOut, ManifestReceive, ParcelOut
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.exceptions import NotFoundError, ForbiddenError
from app.core.pagination import paginate

router = APIRouter(prefix="/api/manifests", tags=["manifests"])


@router.post("", response_model=ManifestOut)
async def create_manifest(
    manifest_in: ManifestCreate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    manifest = TransferManifest(
        origin_branch_id=manifest_in.origin_branch_id,
        destination_branch_id=manifest_in.destination_branch_id,
        driver_name=manifest_in.driver_name,
        vehicle_plate=manifest_in.vehicle_plate,
        notes=manifest_in.notes,
        created_by=current_user.id,
        status=ManifestStatus.IN_TRANSIT
    )
    db.add(manifest)
    await db.flush()
    
    count = 0
    for parcel_id in manifest_in.parcel_ids:
        parcel = await db.get(Parcel, parcel_id)
        if parcel:
            parcel.status = ParcelStatus.IN_TRANSIT
            mp = ManifestParcel(
                manifest_id=manifest.id,
                parcel_id=parcel.id
            )
            db.add(mp)
            count += 1
            
    await db.commit()
    await db.refresh(manifest)
    
    return ManifestOut(
        id=manifest.id,
        origin_branch_id=manifest.origin_branch_id,
        destination_branch_id=manifest.destination_branch_id,
        status=manifest.status,
        driver_name=manifest.driver_name,
        vehicle_plate=manifest.vehicle_plate,
        notes=manifest.notes,
        created_at=manifest.created_at,
        parcel_count=count
    )


@router.get("", response_model=dict)
async def list_manifests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(TransferManifest)
    
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        query = query.where(
            or_(
                TransferManifest.origin_branch_id == current_user.branch_id,
                TransferManifest.destination_branch_id == current_user.branch_id
            )
        )
        
    query = query.order_by(desc(TransferManifest.created_at))
    items, total = await paginate(query, db, page=page, size=size)
    
    manifest_list = []
    for m in items:
        count_q = select(func.count()).select_from(ManifestParcel).where(ManifestParcel.manifest_id == m.id)
        count = await db.scalar(count_q) or 0
        manifest_list.append(ManifestOut(
            id=m.id,
            origin_branch_id=m.origin_branch_id,
            destination_branch_id=m.destination_branch_id,
            status=m.status,
            driver_name=m.driver_name,
            vehicle_plate=m.vehicle_plate,
            notes=m.notes,
            created_at=m.created_at,
            parcel_count=count
        ))
        
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": manifest_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/{manifest_id}", response_model=ManifestDetailOut)
async def get_manifest(
    manifest_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    manifest = await db.get(TransferManifest, manifest_id)
    if not manifest:
        raise NotFoundError("Manifest not found")
        
    mps_q = select(ManifestParcel).where(ManifestParcel.manifest_id == manifest.id)
    mps_res = await db.execute(mps_q)
    mps = mps_res.scalars().all()
    
    parcels = []
    for mp in mps:
        p = await db.get(Parcel, mp.parcel_id)
        if p:
            parcels.append(ParcelOut.model_validate(p))
            
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
        parcels=parcels
    )


@router.post("/{manifest_id}/receive", response_model=ManifestOut)
async def receive_manifest(
    manifest_id: uuid.UUID,
    payload: ManifestReceive,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    manifest = await db.get(TransferManifest, manifest_id)
    if not manifest:
        raise NotFoundError("Manifest not found")
        
    mps_q = select(ManifestParcel).where(ManifestParcel.manifest_id == manifest.id)
    mps_res = await db.execute(mps_q)
    mps = mps_res.scalars().all()
    
    for mp in mps:
        parcel = await db.get(Parcel, mp.parcel_id)
        if not parcel:
            continue
            
        if mp.parcel_id in payload.received_parcel_ids:
            mp.received = True
            mp.received_by = current_user.id
            parcel.status = ParcelStatus.ARRIVED_AT_DESTINATION
        else:
            parcel.status = ParcelStatus.ON_HOLD
            
    manifest.status = ManifestStatus.RECEIVED
    await db.commit()
    await db.refresh(manifest)
    
    return ManifestOut(
        id=manifest.id,
        origin_branch_id=manifest.origin_branch_id,
        destination_branch_id=manifest.destination_branch_id,
        status=manifest.status,
        driver_name=manifest.driver_name,
        vehicle_plate=manifest.vehicle_plate,
        notes=manifest.notes,
        created_at=manifest.created_at,
        parcel_count=len(mps)
    )
