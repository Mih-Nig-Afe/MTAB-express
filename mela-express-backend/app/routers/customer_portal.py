"""Customer portal API — unified BFF for Telegram mini-app, bot, and web."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.core.classification import classify_parcel
from app.core.customer_auth import create_customer_token, decode_customer_token
from app.core.phones import normalize_phone
from app.core.telegram_auth import validate_telegram_init_data
from app.database import get_db
from app.models import Customer, Parcel, ParcelStatus, ContentCategory
from app.models.parcels import SizeCategory
from app.schemas import ParcelOut, ParcelTrackOut
from app.exceptions import NotFoundError
from app.i18n import t
from app.routers.parcels import _parcel_out
from app.routers.parcels import track_parcel as public_track_parcel
from app.services.labels import track_url

router = APIRouter(prefix="/api/customer", tags=["customer-portal"])


class TelegramAuthIn(BaseModel):
    init_data: str = Field(..., description="Telegram.WebApp.initData string")
    phone: str | None = None  # optional link during first mini-app open


class CustomerSessionOut(BaseModel):
    access_token: str
    customer_id: uuid.UUID
    phone: str
    name: str | None = None
    language: str = "en"
    telegram_linked: bool = False


class QuoteIn(BaseModel):
    weight_kg: float = Field(..., gt=0, le=500)
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    content_category: ContentCategory = ContentCategory.GENERAL


class QuoteOut(BaseModel):
    size_category: SizeCategory
    chargeable_weight_kg: float
    suggested_price: float
    estimated_days: str = "1–3"


class PickupCodeOut(BaseModel):
    tracking_code: str
    pickup_code: str
    expires_at: datetime | None
    branch_name: str
    message: str


async def get_current_customer(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer login required")
    try:
        payload = decode_customer_token(authorization[7:])
        customer_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid customer session")

    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found")
    return customer


def _parcel_belongs(parcel: Parcel, customer: Customer) -> bool:
    return (
        parcel.sender_id == customer.id
        or parcel.receiver_id == customer.id
        or normalize_phone(parcel.receiver_phone) == normalize_phone(customer.phone)
    )


@router.post("/auth/telegram", response_model=CustomerSessionOut)
async def auth_telegram(body: TelegramAuthIn, db: AsyncSession = Depends(get_db)):
    """Exchange Telegram WebApp initData for a customer session token."""
    parsed = validate_telegram_init_data(body.init_data)
    if not parsed and settings.environment == "development":
        # Dev fallback: parse initDataUnsafe-style JSON from query for local testing
        user = {}
        if body.phone:
            user = {"id": 0}
        else:
            raise HTTPException(status_code=401, detail="Invalid Telegram session")
    elif not parsed:
        raise HTTPException(status_code=401, detail="Invalid Telegram session")
    else:
        user = parsed.get("user") or {}

    telegram_id = str(user.get("id", ""))
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Telegram user missing")

    result = await db.execute(select(Customer).where(Customer.telegram_id == telegram_id))
    customer = result.scalar_one_or_none()

    if not customer and body.phone:
        phone = normalize_phone(body.phone)
        result = await db.execute(select(Customer).where(Customer.phone == phone))
        customer = result.scalar_one_or_none()
        if customer:
            customer.telegram_id = telegram_id
        else:
            customer = Customer(
                phone=phone,
                telegram_id=telegram_id,
                name=user.get("first_name"),
            )
            db.add(customer)
    elif not customer:
        raise HTTPException(
            status_code=404,
            detail=t("customer.link_phone_bot"),
        )

    if user.get("first_name") and not customer.name:
        customer.name = user.get("first_name")

    await db.commit()
    await db.refresh(customer)

    token = create_customer_token(str(customer.id), telegram_id)
    return CustomerSessionOut(
        access_token=token,
        customer_id=customer.id,
        phone=customer.phone,
        name=customer.name,
        language=customer.language or "en",
        telegram_linked=True,
    )


@router.get("/me", response_model=CustomerSessionOut)
async def customer_me(customer: Customer = Depends(get_current_customer)):
    return CustomerSessionOut(
        access_token="",
        customer_id=customer.id,
        phone=customer.phone,
        name=customer.name,
        language=customer.language or "en",
        telegram_linked=bool(customer.telegram_id),
    )


@router.get("/parcels", response_model=List[ParcelOut])
async def my_parcels(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    phone = normalize_phone(customer.phone)
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
    rows = (await db.execute(query)).scalars().unique().all()
    return [_parcel_out(p) for p in rows]


@router.get("/parcels/{tracking_code}", response_model=ParcelTrackOut)
async def my_parcel_track(
    tracking_code: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    data = await public_track_parcel(tracking_code.upper(), db)
    result = await db.execute(select(Parcel).where(Parcel.tracking_code == tracking_code.upper()))
    parcel = result.scalar_one_or_none()
    if parcel and not _parcel_belongs(parcel, customer):
        raise HTTPException(status_code=403, detail="This parcel is not linked to your account")
    return data


@router.get("/pickup-code/{tracking_code}", response_model=PickupCodeOut)
async def pickup_code(
    tracking_code: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Parcel)
        .options(joinedload(Parcel.destination_branch))
        .where(Parcel.tracking_code == tracking_code.upper())
    )
    parcel = result.scalar_one_or_none()
    if not parcel or not _parcel_belongs(parcel, customer):
        raise NotFoundError("Parcel not found")
    if parcel.status != ParcelStatus.READY_FOR_PICKUP:
        raise HTTPException(status_code=409, detail="Parcel is not ready for pickup yet")
    if not parcel.pickup_otp:
        parcel.pickup_otp = f"{secrets.randbelow(900000) + 100000:06d}"
        parcel.otp_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.commit()
        await db.refresh(parcel)

    from app.i18n import t
    lang = customer.language or "en"
    return PickupCodeOut(
        tracking_code=parcel.tracking_code,
        pickup_code=parcel.pickup_otp,
        expires_at=parcel.otp_expires_at,
        branch_name=parcel.destination_branch.name if parcel.destination_branch else "",
        message=t("customer.pickup_code_hint", lang=lang),
    )


@router.post("/parcels/{tracking_code}/confirm-receipt")
async def customer_confirm_receipt(
    tracking_code: str,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    from app.models import ParcelStatusHistory

    result = await db.execute(select(Parcel).where(Parcel.tracking_code == tracking_code.upper()))
    parcel = result.scalar_one_or_none()
    if not parcel or not _parcel_belongs(parcel, customer):
        raise NotFoundError("Parcel not found")
    if parcel.status != ParcelStatus.DELIVERED:
        raise HTTPException(status_code=409, detail="Parcel is not delivered yet")

    db.add(ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=ParcelStatus.DELIVERED,
        to_status=ParcelStatus.DELIVERED,
        note="Receiver confirmed receipt via customer portal",
    ))
    await db.commit()
    return {"status": "ok", "tracking_code": parcel.tracking_code}


@router.post("/quote", response_model=QuoteOut)
async def price_quote(body: QuoteIn):
    result = classify_parcel(
        weight_kg=body.weight_kg,
        length_cm=body.length_cm,
        width_cm=body.width_cm,
        height_cm=body.height_cm,
        content_category=body.content_category,
    )
    return QuoteOut(
        size_category=result.size_category,
        chargeable_weight_kg=float(result.chargeable_weight_kg),
        suggested_price=float(result.suggested_price),
    )


@router.get("/branches")
async def customer_branches(db: AsyncSession = Depends(get_db)):
    from app.models import Branch

    result = await db.execute(
        select(Branch).where(Branch.is_active == True).order_by(Branch.city, Branch.name)
    )
    return [
        {
            "name": b.name,
            "code": b.code,
            "city": b.city,
            "phone": b.phone,
            "facility_type": b.facility_type.value if b.facility_type else "branch",
            "airport_iata": b.airport_iata,
        }
        for b in result.scalars().all()
    ]


@router.get("/track-url/{tracking_code}")
async def track_deep_link(tracking_code: str):
    return {
        "tracking_code": tracking_code.upper(),
        "web_url": track_url(tracking_code.upper()),
        "portal_url": f"{settings.public_portal_url.rstrip('/')}/track/{tracking_code.upper()}",
    }
