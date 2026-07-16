from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional
import uuid

from app.database import get_db
from app.models import (
    Parcel, ParcelStatus, ParcelStatusHistory, Customer, Branch, StaffUser, StaffRole, PaymentMode, PaymentStatus, ParcelProofOfDelivery
)
from app.schemas import (
    ParcelCreate, ParcelOut, ParcelDetailOut, ParcelStatusUpdate, ParcelTrackOut, ProofOfDeliveryUpload
)
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.core.tracking_code import generate_tracking_code
from app.core.state_machine import validate_transition, InvalidTransition
from app.core.pagination import paginate
from app.exceptions import NotFoundError, ForbiddenError, PaymentRequired
from app.services.notifications import notify_status_change

router = APIRouter(prefix="/api/parcels", tags=["parcels"])


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
        declared_value=parcel_in.declared_value,
        price=parcel_in.price,
        payment_mode=parcel_in.payment_mode,
        payment_method=parcel_in.payment_method,
        status=ParcelStatus.CREATED,
        created_by=current_user.id
    )
    db.add(parcel)
    await db.flush()
    
    history = ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=None,
        to_status=ParcelStatus.CREATED,
        changed_by=current_user.id,
        branch_id=parcel_in.origin_branch_id,
        note="Parcel created"
    )
    db.add(history)
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.get("", response_model=dict)
async def list_parcels(
    status_filter: Optional[ParcelStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Parcel)
    
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
        
    query = query.order_by(desc(Parcel.created_at))
    items, total = await paginate(query, db, page=page, size=size)
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": [ParcelOut.model_validate(p) for p in items],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/{parcel_id}", response_model=ParcelDetailOut)
async def get_parcel(
    parcel_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Parcel).options(
        selectinload(Parcel.status_history)
    ).where(Parcel.id == parcel_id)
    
    result = await db.execute(query)
    parcel = result.scalar_one_or_none()
    
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        if parcel.origin_branch_id != current_user.branch_id and parcel.destination_branch_id != current_user.branch_id:
            raise ForbiddenError("You don't have access to this parcel")
            
    return parcel


@router.get("/track/{tracking_code}", response_model=ParcelTrackOut)
async def track_parcel(
    tracking_code: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Parcel).options(
        joinedload(Parcel.origin_branch),
        joinedload(Parcel.destination_branch),
        selectinload(Parcel.status_history)
    ).where(Parcel.tracking_code == tracking_code)
    
    result = await db.execute(query)
    parcel = result.scalar_one_or_none()
    
    if not parcel:
        raise NotFoundError("Parcel not found")
        
    return ParcelTrackOut(
        tracking_code=parcel.tracking_code,
        status=parcel.status,
        payment_status=parcel.payment_status,
        origin_branch_name=parcel.origin_branch.name if parcel.origin_branch else "",
        destination_branch_name=parcel.destination_branch.name if parcel.destination_branch else "",
        status_history=parcel.status_history,
        created_at=parcel.created_at
    )


@router.patch("/{parcel_id}/status", response_model=ParcelDetailOut)
async def update_status(
    parcel_id: uuid.UUID,
    status_in: ParcelStatusUpdate,
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
        
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        if parcel.origin_branch_id != current_user.branch_id and parcel.destination_branch_id != current_user.branch_id:
            raise ForbiddenError("You don't have access to this parcel")

    try:
        validate_transition(parcel.status, status_in.to_status)
    except InvalidTransition as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if parcel.payment_mode == PaymentMode.BEFORE and parcel.payment_status != PaymentStatus.PAID:
        restricted_statuses = [
            ParcelStatus.IN_TRANSIT,
            ParcelStatus.ARRIVED_AT_DESTINATION,
            ParcelStatus.READY_FOR_PICKUP,
            ParcelStatus.DELIVERED
        ]
        if status_in.to_status in restricted_statuses:
            raise PaymentRequired("Payment required before proceeding")
            
    from_status = parcel.status
    parcel.status = status_in.to_status
    
    history = ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=from_status,
        to_status=status_in.to_status,
        changed_by=current_user.id,
        branch_id=current_user.branch_id or parcel.destination_branch_id,
        note=status_in.note
    )
    db.add(history)
    await db.commit()
    await db.refresh(parcel)
    
    sender = await db.get(Customer, parcel.sender_id)
    dest_branch = await db.get(Branch, parcel.destination_branch_id)
    if sender and sender.telegram_id:
        await notify_status_change(
            telegram_id=sender.telegram_id,
            tracking_code=parcel.tracking_code,
            branch_name=dest_branch.name if dest_branch else "",
            to_status=status_in.to_status,
            note=status_in.note,
        )
    return parcel


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
