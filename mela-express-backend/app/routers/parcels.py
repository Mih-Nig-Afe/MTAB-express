import random
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Parcel, ParcelStatusHistory, Customer, Branch, ParcelStatus
from app.schemas import ParcelCreate, ParcelOut, ParcelStatusUpdate
from app.services.notifications import notify_status_change

router = APIRouter(prefix="/api/parcels", tags=["parcels"])


async def _get_or_create_customer(db: AsyncSession, phone: str) -> Customer:
    result = await db.execute(select(Customer).where(Customer.phone == phone))
    customer = result.scalar_one_or_none()
    if customer is None:
        customer = Customer(phone=phone)
        db.add(customer)
        await db.flush()
    return customer


async def _generate_tracking_code(db: AsyncSession, origin_branch: Branch) -> str:
    """
    Branch-prefixed, non-sequential code — e.g. MEX-HW-4821.
    Non-sequential on purpose: a guessable/sequential code leaks shipment
    volume to anyone who cares to enumerate it.
    """
    prefix = f"MEX-{origin_branch.city[:2].upper()}"
    for _ in range(5):  # retry a handful of times on collision, astronomically unlikely
        candidate = f"{prefix}-{random.randint(1000, 9999)}"
        existing = await db.execute(select(Parcel).where(Parcel.tracking_code == candidate))
        if existing.scalar_one_or_none() is None:
            return candidate
    raise HTTPException(500, "Could not generate a unique tracking code, retry")


@router.post("", response_model=ParcelOut)
async def create_parcel(payload: ParcelCreate, created_by: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """created_by would normally come from an auth dependency (the logged-in operator), not a query param — wired simply here for clarity."""
    origin = await db.get(Branch, payload.origin_branch_id)
    if origin is None:
        raise HTTPException(404, "Origin branch not found")

    sender = await _get_or_create_customer(db, payload.sender_phone)
    tracking_code = await _generate_tracking_code(db, origin)

    parcel = Parcel(
        tracking_code=tracking_code,
        origin_branch_id=payload.origin_branch_id,
        destination_branch_id=payload.destination_branch_id,
        sender_id=sender.id,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        description=payload.description,
        weight_kg=payload.weight_kg,
        declared_value=payload.declared_value,
        price=payload.price,
        payment_mode=payload.payment_mode,
        payment_method=payload.payment_method,
        status=ParcelStatus.CREATED,
        created_by=created_by,
    )
    db.add(parcel)
    await db.flush()

    db.add(ParcelStatusHistory(
        parcel_id=parcel.id, from_status=None, to_status=ParcelStatus.CREATED,
        changed_by=created_by, branch_id=payload.origin_branch_id,
    ))
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.get("/track/{tracking_code}", response_model=ParcelOut)
async def track_parcel(tracking_code: str, db: AsyncSession = Depends(get_db)):
    """Public-ish lookup used by both the Telegram bot and a future web tracking page.
    Rate-limit this endpoint at the gateway level — it's the one most exposed to enumeration."""
    result = await db.execute(select(Parcel).where(Parcel.tracking_code == tracking_code))
    parcel = result.scalar_one_or_none()
    if parcel is None:
        raise HTTPException(404, "No parcel found with that tracking code")
    return parcel


@router.patch("/{parcel_id}/status", response_model=ParcelOut)
async def update_status(parcel_id: uuid.UUID, payload: ParcelStatusUpdate,
                         changed_by: uuid.UUID, db: AsyncSession = Depends(get_db)):
    parcel = await db.get(Parcel, parcel_id)
    if parcel is None:
        raise HTTPException(404, "Parcel not found")

    from_status = parcel.status
    parcel.status = payload.to_status
    db.add(ParcelStatusHistory(
        parcel_id=parcel.id, from_status=from_status, to_status=payload.to_status,
        changed_by=changed_by, branch_id=parcel.destination_branch_id, note=payload.note,
    ))
    await db.commit()
    await db.refresh(parcel)

    sender = await db.get(Customer, parcel.sender_id)
    dest_branch = await db.get(Branch, parcel.destination_branch_id)
    if sender and sender.telegram_id:
        await notify_status_change(
            telegram_id=sender.telegram_id, tracking_code=parcel.tracking_code,
            branch_name=dest_branch.name if dest_branch else "", to_status=payload.to_status,
            note=payload.note,
        )
    return parcel
