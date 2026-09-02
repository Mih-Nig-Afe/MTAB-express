from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List
import secrets
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import Customer, Parcel, ParcelStatus
from app.schemas import CustomerLink, CustomerOut, ParcelOut, CustomerLanguageUpdate
from app.core.phones import normalize_phone
from app.routers.parcels import _parcel_out

from app.exceptions import NotFoundError

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("/telegram/{telegram_id}", response_model=CustomerOut)
async def get_customer_by_telegram(telegram_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.telegram_id == str(telegram_id)))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer not found")
    return customer

@router.post("/link", response_model=CustomerOut)
async def link_customer(request: CustomerLink, db: AsyncSession = Depends(get_db)):
    request.phone = normalize_phone(request.phone)

    # Match by phone first, then by telegram_id. The second lookup makes
    # re-linking idempotent: a customer who linked before (possibly with an
    # un-normalized phone) updates their existing row instead of triggering
    # a unique-constraint violation on telegram_id.
    result = await db.execute(select(Customer).where(Customer.phone == request.phone))
    customer = result.scalar_one_or_none()
    if not customer:
        result = await db.execute(
            select(Customer).where(Customer.telegram_id == str(request.telegram_id))
        )
        customer = result.scalar_one_or_none()

    if customer:
        customer.phone = request.phone
        if request.telegram_id:
            customer.telegram_id = str(request.telegram_id)
        if request.name:
            customer.name = request.name
    else:
        customer = Customer(
            phone=request.phone,
            name=request.name or "Unknown",
            telegram_id=request.telegram_id
        )
        db.add(customer)

    await db.commit()
    await db.refresh(customer)
    return customer

@router.get("/me/parcels", response_model=List[ParcelOut])
async def get_my_parcels(phone: str, db: AsyncSession = Depends(get_db)):
    phone = normalize_phone(phone)
    result = await db.execute(select(Customer).where(Customer.phone == phone))
    customer = result.scalar_one_or_none()

    if not customer:
        return []

    query = (
        select(Parcel)
        .options(
            joinedload(Parcel.origin_branch),
            joinedload(Parcel.destination_branch),
            joinedload(Parcel.sender),
        )
        .where(
            or_(
                Parcel.sender_id == customer.id,
                Parcel.receiver_id == customer.id,
                Parcel.receiver_phone == phone,
            )
        )
        .order_by(Parcel.created_at.desc())
        .limit(50)
    )

    parcels_result = await db.execute(query)
    return [_parcel_out(p) for p in parcels_result.scalars().unique().all()]


@router.get("/telegram/{telegram_id}/pickup-code/{tracking_code}")
async def telegram_pickup_code(telegram_id: str, tracking_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.telegram_id == str(telegram_id)))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer not found")

    result = await db.execute(
        select(Parcel)
        .options(joinedload(Parcel.destination_branch))
        .where(Parcel.tracking_code == tracking_code.upper())
    )
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise NotFoundError("Parcel not found")

    phone = normalize_phone(customer.phone)
    belongs = (
        parcel.sender_id == customer.id
        or parcel.receiver_id == customer.id
        or normalize_phone(parcel.receiver_phone) == phone
    )
    if not belongs:
        raise HTTPException(status_code=403, detail="This parcel is not linked to your account")
    if parcel.status != ParcelStatus.READY_FOR_PICKUP:
        raise HTTPException(status_code=409, detail="Parcel is not ready for pickup yet")

    if not parcel.pickup_otp:
        parcel.pickup_otp = f"{secrets.randbelow(900000) + 100000:06d}"
        parcel.otp_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.commit()
        await db.refresh(parcel)

    return {
        "tracking_code": parcel.tracking_code,
        "pickup_code": parcel.pickup_otp,
        "expires_at": parcel.otp_expires_at,
        "branch_name": parcel.destination_branch.name if parcel.destination_branch else "",
    }


@router.post("/language", response_model=CustomerOut)
async def set_customer_language(request: CustomerLanguageUpdate, db: AsyncSession = Depends(get_db)):
    """Persist a customer's preferred message language (Telegram /lang)."""
    if request.language not in ("en", "am"):
        raise HTTPException(status_code=422, detail="language must be 'en' or 'am'")

    customer = None
    if request.phone:
        result = await db.execute(select(Customer).where(Customer.phone == normalize_phone(request.phone)))
        customer = result.scalar_one_or_none()
    if not customer and request.telegram_id:
        result = await db.execute(
            select(Customer).where(Customer.telegram_id == str(request.telegram_id))
        )
        customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer not found")

    customer.language = request.language
    await db.commit()
    await db.refresh(customer)
    return customer
