from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional
import uuid
from datetime import date, datetime, timedelta, timezone

from app.database import get_db
from app.models import (
    Parcel, ParcelStatus, ParcelStatusHistory, Customer, Branch, StaffUser, StaffRole, PaymentMode, PaymentStatus, ParcelProofOfDelivery,
    TransferManifest, ManifestParcel, ManifestCheckpoint, ParcelJourneyEvent,
)
from app.schemas import (
    ParcelCreate, ParcelOut, ParcelDetailOut, ParcelStatusUpdate, ParcelTrackOut, ProofOfDeliveryUpload,
    OTPGenerateOut, VerifyPickupRequest, FlightLegAttach,
    ClassificationPreview, ClassificationPreviewOut, ParcelScanRequest, ParcelScanOut,
)
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.core.tracking_code import generate_tracking_code
from app.core.state_machine import payment_gated, validate_transition, InvalidTransition
from app.core.classification import classify_parcel
from app.core.scan_workflow import normalize_scan_code, resolve_scan, ScanError, ScanFailure
from app.core.pagination import paginate
from app.exceptions import NotFoundError, ForbiddenError, PaymentRequired
from app.services.journey import (
    load_parcel_for_update,
    notify_after_scan,
    record_scan,
    seed_parcel_plan,
    tracking_extras,
    upsert_flight_leg,
)
from app.services.labels import sticker_html, track_url, barcode_svg, qr_svg
from app.core.carrier_status import carrier_label, carrier_code
from app.i18n import t as i18n_t

router = APIRouter(prefix="/api/parcels", tags=["parcels"])


def _parcel_out(parcel: Parcel) -> ParcelOut:
    data = ParcelOut.model_validate(parcel).model_dump()
    data["track_url"] = track_url(parcel.tracking_code)
    if getattr(parcel, "origin_branch", None):
        data["origin_branch_code"] = parcel.origin_branch.code
    if getattr(parcel, "destination_branch", None):
        data["destination_branch_code"] = parcel.destination_branch.code
    if getattr(parcel, "sender", None):
        data["sender_phone"] = parcel.sender.phone
    return ParcelOut.model_validate(data)


@router.post("/classify-preview", response_model=ClassificationPreviewOut)
async def preview_classification(
    body: ClassificationPreview,
    _: CurrentUser = Depends(get_current_user),
):
    result = classify_parcel(
        weight_kg=body.weight_kg,
        length_cm=body.length_cm,
        width_cm=body.width_cm,
        height_cm=body.height_cm,
        content_category=body.content_category,
    )
    return ClassificationPreviewOut(
        size_category=result.size_category,
        volumetric_weight_kg=result.volumetric_weight_kg,
        chargeable_weight_kg=result.chargeable_weight_kg,
        suggested_price=result.suggested_price,
    )


@router.post("/scan", response_model=ParcelScanOut)
async def scan_parcel(
    body: ParcelScanRequest,
    current_user: CurrentUser = Depends(
        require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.DRIVER, StaffRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Barcode/QR scan station — advances status from staff branch + role context."""
    code = normalize_scan_code(body.code)
    if not code:
        raise HTTPException(status_code=400, detail="Empty scan code")

    result = await db.execute(select(Parcel).where(Parcel.tracking_code == code))
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise NotFoundError(f"No parcel found for {code}")

    branch = await db.get(Branch, current_user.branch_id) if current_user.branch_id else None
    resolution = resolve_scan(parcel, branch, role=current_user.role)
    if isinstance(resolution, ScanFailure):
        status_code = {
            ScanError.WRONG_STATION: 409,
            ScanError.PAYMENT_REQUIRED: 402,
            ScanError.TERMINAL: 409,
            ScanError.NO_TRANSITION: 409,
        }.get(resolution.error, 400)
        raise HTTPException(status_code=status_code, detail=resolution.message)

    to_status = resolution.to_status
    if parcel.payment_mode == PaymentMode.BEFORE and parcel.payment_status != PaymentStatus.PAID:
        if payment_gated(to_status):
            raise PaymentRequired("Prepaid parcel — collect payment before dispatch.")

    if to_status in (ParcelStatus.CHECKED_IN_FLIGHT, ParcelStatus.DEPARTED) and not body.flight_number:
        raise HTTPException(
            status_code=400,
            detail="Enter flight number at airport check-in scan.",
        )

    parcel = await load_parcel_for_update(db, parcel.id)
    from_status = parcel.status
    flight_payload = body if body.flight_number else None
    parcel = await record_scan(
        db,
        parcel,
        to_status=to_status,
        staff_id=current_user.id,
        branch_id=current_user.branch_id,
        note=body.note or resolution.note,
        location_name=resolution.station_label,
        flight_payload=flight_payload,
        source="barcode",
    )
    await db.commit()
    parcel = await load_parcel_for_update(db, parcel.id)
    await notify_after_scan(db, parcel, to_status, body.note or resolution.note)
    await db.commit()

    return ParcelScanOut(
        tracking_code=parcel.tracking_code,
        from_status=from_status,
        to_status=to_status,
        status_label=i18n_t(f"parcel_status.{to_status.value}"),
        station=resolution.station_label,
        message=f"Updated to {i18n_t(f'parcel_status.{to_status.value}')}",
        track_url=track_url(parcel.tracking_code),
    )


async def _get_or_create_customer(db: AsyncSession, phone: str, name: str | None = None) -> Customer:
    result = await db.execute(select(Customer).where(Customer.phone == phone))
    customer = result.scalar_one_or_none()
    if not customer:
        customer = Customer(phone=phone, name=name)
        db.add(customer)
        await db.flush()
    elif name and not customer.name:
        customer.name = name
    return customer


@router.post("", response_model=ParcelOut)
async def create_parcel(
    parcel_in: ParcelCreate, 
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    sender = await _get_or_create_customer(db, parcel_in.sender_phone, parcel_in.sender_name)
    receiver = await _get_or_create_customer(db, parcel_in.receiver_phone, parcel_in.receiver_name)
    
    branch = await db.get(Branch, parcel_in.origin_branch_id)
    if not branch:
        raise NotFoundError("Origin branch not found")
        
    tracking_code = await generate_tracking_code(branch.code, db)
    classified = classify_parcel(
        weight_kg=parcel_in.weight_kg,
        length_cm=parcel_in.length_cm,
        width_cm=parcel_in.width_cm,
        height_cm=parcel_in.height_cm,
        content_category=parcel_in.content_category,
    )
    price = parcel_in.price if parcel_in.price is not None else classified.suggested_price
    
    parcel = Parcel(
        tracking_code=tracking_code,
        origin_branch_id=parcel_in.origin_branch_id,
        destination_branch_id=parcel_in.destination_branch_id,
        sender_id=sender.id,
        receiver_id=receiver.id,
        receiver_name=parcel_in.receiver_name,
        receiver_phone=parcel_in.receiver_phone,
        description=parcel_in.description,
        weight_kg=parcel_in.weight_kg,
        length_cm=parcel_in.length_cm,
        width_cm=parcel_in.width_cm,
        height_cm=parcel_in.height_cm,
        size_category=parcel_in.size_category or classified.size_category,
        content_category=parcel_in.content_category,
        volumetric_weight_kg=classified.volumetric_weight_kg,
        chargeable_weight_kg=classified.chargeable_weight_kg,
        declared_value=parcel_in.declared_value,
        price=price,
        payment_mode=parcel_in.payment_mode,
        payment_method=parcel_in.payment_method,
        status=ParcelStatus.RECEIVED_AT_ORIGIN,
        created_by=current_user.id
    )
    db.add(parcel)
    await db.flush()
    
    history = ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=ParcelStatus.CREATED,
        to_status=ParcelStatus.RECEIVED_AT_ORIGIN,
        changed_by=current_user.id,
        branch_id=parcel_in.origin_branch_id,
        note="Drop-off intake — tracking sticker issued"
    )
    db.add(history)
    db.add(ParcelJourneyEvent(
        parcel_id=parcel.id,
        event_type=ParcelStatus.RECEIVED_AT_ORIGIN.value,
        to_status=ParcelStatus.RECEIVED_AT_ORIGIN,
        location_name=branch.name,
        facility_type=branch.facility_type.value if branch else "branch",
        source="intake",
        actor_staff_id=current_user.id,
        note="Drop-off intake — tracking sticker issued",
    ))
    await db.flush()
    await seed_parcel_plan(db, parcel)
    await db.commit()
    loaded = (await db.execute(
        select(Parcel)
        .options(
            joinedload(Parcel.origin_branch),
            joinedload(Parcel.destination_branch),
            joinedload(Parcel.sender),
        )
        .where(Parcel.id == parcel.id)
    )).scalar_one()
    return _parcel_out(loaded)


@router.get("", response_model=dict)
async def list_parcels(
    status_filter: Optional[ParcelStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    created_from: Optional[date] = Query(None, description="Inclusive created date (YYYY-MM-DD)"),
    created_to: Optional[date] = Query(None, description="Inclusive created date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Parcel).options(
        joinedload(Parcel.origin_branch),
        joinedload(Parcel.destination_branch),
        joinedload(Parcel.sender),
    )
    
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        query = query.where(
            or_(
                Parcel.origin_branch_id == current_user.branch_id,
                Parcel.destination_branch_id == current_user.branch_id
            )
        )
        
    if status_filter:
        query = query.where(Parcel.status == status_filter)
    if search:
        query = query.where(Parcel.tracking_code.ilike(f"%{search}%"))
    if created_from:
        start_dt = datetime.combine(created_from, datetime.min.time()).replace(tzinfo=timezone.utc)
        query = query.where(Parcel.created_at >= start_dt)
    if created_to:
        end_dt = datetime.combine(created_to + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)
        query = query.where(Parcel.created_at < end_dt)
        
    query = query.order_by(desc(Parcel.created_at))
    items, total = await paginate(query, db, page=page, size=size)
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": [_parcel_out(p) for p in items],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/track/{tracking_code}", response_model=ParcelTrackOut)
async def track_parcel(
    tracking_code: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Parcel).options(
        joinedload(Parcel.origin_branch),
        joinedload(Parcel.destination_branch),
        selectinload(Parcel.status_history),
        selectinload(Parcel.journey_events),
        selectinload(Parcel.flight_legs),
    ).where(Parcel.tracking_code == tracking_code)

    result = await db.execute(query)
    parcel = result.scalar_one_or_none()

    if not parcel:
        raise NotFoundError("Parcel not found")

    # Live route checkpoints from any manifests carrying this parcel.
    checkpoint_rows = (await db.execute(
        select(ManifestCheckpoint)
        .join(ManifestParcel, ManifestCheckpoint.manifest_id == ManifestParcel.manifest_id)
        .where(ManifestParcel.parcel_id == parcel.id)
        .order_by(ManifestCheckpoint.created_at.asc())
    )).scalars().all()

    extras = tracking_extras(parcel)
    return ParcelTrackOut(
        tracking_code=parcel.tracking_code,
        status=parcel.status,
        payment_status=parcel.payment_status,
        origin_branch_name=parcel.origin_branch.name if parcel.origin_branch else "",
        destination_branch_name=parcel.destination_branch.name if parcel.destination_branch else "",
        status_history=parcel.status_history,
        checkpoints=checkpoint_rows,
        journey_events=extras["journey_events"],
        flight=extras["flight"],
        eta=extras["eta"],
        created_at=parcel.created_at
    )


@router.get("/{parcel_id}", response_model=ParcelDetailOut)
async def get_parcel(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    parcel = await load_parcel_for_update(db, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        if parcel.origin_branch_id != current_user.branch_id and parcel.destination_branch_id != current_user.branch_id:
            raise ForbiddenError("You don't have access to this parcel")

    extras = tracking_extras(parcel)
    return ParcelDetailOut.model_validate(parcel).model_copy(update=extras)


@router.patch("/{parcel_id}/status", response_model=ParcelDetailOut)
async def update_status(
    parcel_id: uuid.UUID,
    status_in: ParcelStatusUpdate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Manual status override — admin/manager only. Operators use scan stations."""
    parcel = await load_parcel_for_update(db, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        if parcel.origin_branch_id != current_user.branch_id and parcel.destination_branch_id != current_user.branch_id:
            raise ForbiddenError("You don't have access to this parcel")

    try:
        validate_transition(parcel.status, status_in.to_status)
    except InvalidTransition as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if parcel.payment_mode == PaymentMode.BEFORE and parcel.payment_status != PaymentStatus.PAID:
        if payment_gated(status_in.to_status):
            raise PaymentRequired("Payment required before proceeding")

    if status_in.to_status in (
        ParcelStatus.CHECKED_IN_FLIGHT,
        ParcelStatus.DEPARTED,
    ) and not status_in.flight_number and not parcel.flight_legs:
        raise HTTPException(
            status_code=400,
            detail="Flight number is required when checking in or departing a flight.",
        )

    parcel = await record_scan(
        db,
        parcel,
        to_status=status_in.to_status,
        staff_id=current_user.id,
        branch_id=current_user.branch_id or parcel.destination_branch_id,
        note=status_in.note,
        location_name=status_in.location_name,
        latitude=status_in.latitude,
        longitude=status_in.longitude,
        flight_payload=status_in if status_in.flight_number else None,
    )
    await db.commit()
    parcel = await load_parcel_for_update(db, parcel.id)
    await notify_after_scan(db, parcel, status_in.to_status, status_in.note)
    extras = tracking_extras(parcel)
    return ParcelDetailOut.model_validate(parcel).model_copy(update=extras)


@router.patch("/{parcel_id}/flight", response_model=ParcelDetailOut)
async def attach_flight(
    parcel_id: uuid.UUID,
    flight_in: FlightLegAttach,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    parcel = await load_parcel_for_update(db, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
    try:
        await upsert_flight_leg(db, parcel, flight_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await db.commit()
    parcel = await load_parcel_for_update(db, parcel.id)
    extras = tracking_extras(parcel)
    return ParcelDetailOut.model_validate(parcel).model_copy(update=extras)


@router.get("/{parcel_id}/sticker", response_class=HTMLResponse)
async def print_sticker(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
    origin = await db.get(Branch, parcel.origin_branch_id)
    dest = await db.get(Branch, parcel.destination_branch_id)
    sender = await db.get(Customer, parcel.sender_id)
    html = sticker_html({
        "tracking_code": parcel.tracking_code,
        "origin_branch": origin.name if origin else "",
        "destination_branch": dest.name if dest else "",
        "sender_phone": sender.phone if sender else "",
        "receiver_name": parcel.receiver_name,
        "receiver_phone": parcel.receiver_phone,
        "weight_kg": parcel.weight_kg,
        "chargeable_weight_kg": parcel.chargeable_weight_kg,
        "size_category": parcel.size_category.value if parcel.size_category else "",
        "content_category": parcel.content_category.value if parcel.content_category else "",
        "price": parcel.price,
        "payment_badge": "PAID" if parcel.payment_status == PaymentStatus.PAID else "COLLECT",
        "created_at": parcel.created_at.strftime("%Y-%m-%d") if parcel.created_at else "",
    })
    return HTMLResponse(content=html)


@router.get("/{parcel_id}/barcode.svg")
async def parcel_barcode(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
    return Response(content=barcode_svg(parcel.tracking_code), media_type="image/svg+xml")


@router.get("/{parcel_id}/qr.svg")
async def parcel_qr(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
    return Response(content=qr_svg(track_url(parcel.tracking_code)), media_type="image/svg+xml")


@router.get("/{parcel_id}/waybill")
async def get_waybill(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
    return {"waybill_url": parcel.waybill_url or f"https://mela-express.com/waybill/{parcel_id}.pdf"}


@router.post("/{parcel_id}/proof")
async def upload_proof(
    parcel_id: uuid.UUID,
    proof_in: ProofOfDeliveryUpload,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    proof = ParcelProofOfDelivery(
        parcel_id=parcel.id,
        photo_url=proof_in.photo_url,
        signature_url=proof_in.signature_url,
        notes=proof_in.notes,
        created_by=current_user.id
    )
    db.add(proof)
    
    from_status = parcel.status
    parcel.status = ParcelStatus.DELIVERED
    history = ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=from_status,
        to_status=ParcelStatus.DELIVERED,
        changed_by=current_user.id,
        branch_id=current_user.branch_id or parcel.destination_branch_id,
        note="Proof of delivery uploaded"
    )
    db.add(history)
    
    await db.commit()
    return {"message": "Proof of delivery uploaded successfully"}


@router.post("/{parcel_id}/otp", response_model=OTPGenerateOut)
async def generate_pickup_otp(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    import random
    from datetime import datetime, timedelta, timezone

    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    otp = f"{random.randint(100000, 999999)}"
    parcel.pickup_otp = otp
    parcel.otp_expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
    
    await db.commit()
    
    return OTPGenerateOut(
        parcel_id=parcel.id,
        tracking_code=parcel.tracking_code,
        pickup_otp=otp,
        receiver_phone=parcel.receiver_phone,
        message=f"OTP generated and sent to {parcel.receiver_phone}"
    )


@router.post("/{parcel_id}/verify-pickup", response_model=ParcelDetailOut)
async def verify_pickup_otp(
    parcel_id: uuid.UUID,
    payload: VerifyPickupRequest,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Parcel).options(
            selectinload(Parcel.status_history)
        ).where(Parcel.id == parcel_id)
    )
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    if parcel.payment_mode == PaymentMode.AFTER and parcel.payment_status != PaymentStatus.PAID:
        raise PaymentRequired("Cash payment of delivery fee must be collected before handover.")
        
    # OTP must have been generated for this parcel, must match exactly,
    # and must not be expired (72h window set at generation time).
    if not parcel.pickup_otp:
        raise HTTPException(
            status_code=400,
            detail="No pickup OTP was generated for this parcel. Generate one first."
        )
    if parcel.otp_expires_at and datetime.now(timezone.utc) > parcel.otp_expires_at:
        raise HTTPException(status_code=400, detail="This OTP has expired. Please generate a new one.")
    if parcel.pickup_otp != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP code entered. Please verify with the receiver.")
        
    proof = ParcelProofOfDelivery(
        parcel_id=parcel.id,
        photo_url=payload.photo_url or "https://mela-express.com/proof/default.jpg",
        signature_url=payload.signature_url,
        notes=payload.notes or "Verified via SMS/Telegram OTP at destination branch",
        created_by=current_user.id
    )
    db.add(proof)
    
    from_status = parcel.status
    parcel.status = ParcelStatus.DELIVERED
    parcel.pickup_otp = None
    
    history = ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=from_status,
        to_status=ParcelStatus.DELIVERED,
        changed_by=current_user.id,
        branch_id=current_user.branch_id or parcel.destination_branch_id,
        note=f"Handover verified via OTP. Signature: {'Captured' if payload.signature_url else 'None'}"
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(parcel)
    return parcel



@router.post("/track/{tracking_code}/confirm_receipt")
async def confirm_receipt(
    tracking_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Receiver-side acknowledgment (no auth): customer taps 'Confirm Receipt'
    in the Telegram bot after a parcel is marked DELIVERED."""
    result = await db.execute(
        select(Parcel).where(Parcel.tracking_code == tracking_code.upper())
    )
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise NotFoundError("Parcel not found")
    if parcel.status != ParcelStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Parcel is not delivered yet (current status: {parcel.status.value})"
        )

    db.add(ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=ParcelStatus.DELIVERED,
        to_status=ParcelStatus.DELIVERED,
        note="Receiver confirmed receipt via Telegram bot",
    ))
    await db.commit()
    return {"status": "ok", "tracking_code": parcel.tracking_code}
