from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.models import Parcel, Payment, PaymentStatus, PaymentMethod, StaffRole, Customer
from app.schemas import CashCollectRequest, ChapaInitRequest
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.exceptions import NotFoundError, ForbiddenError
from app.services import chapa
from app.config import settings
from app.services.notifications import notify_payment_confirmed

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/cash/{parcel_id}/collect")
async def collect_cash(
    parcel_id: uuid.UUID,
    request: CashCollectRequest,
    current_user: CurrentUser = Depends(require_roles(StaffRole.OPERATOR, StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    parcel = await db.get(Parcel, parcel_id)
    if not parcel:
        raise NotFoundError("Parcel not found")

    # Idempotency guard: never double-collect (corrupts reconciliation totals).
    if parcel.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=409,
            detail="Payment for this parcel was already collected."
        )

    payment = Payment(
        parcel_id=parcel.id,
        amount=parcel.price,
        method=PaymentMethod.CASH,
        status=PaymentStatus.PAID,
        collected_by=current_user.id,
        override_reason=request.override_reason
    )
    db.add(payment)
    
    parcel.payment_status = PaymentStatus.PAID
    parcel.payment_method = PaymentMethod.CASH
    await db.commit()
    await db.refresh(parcel)
    
    sender = await db.get(Customer, parcel.sender_id)
    await notify_payment_confirmed(
        db=db,
        customer_id=parcel.sender_id,
        phone=sender.phone if sender else None,
        telegram_id=sender.telegram_id if sender else None,
        tracking_code=parcel.tracking_code,
        amount=float(parcel.price),
        parcel_id=parcel.id
    )
    return {"message": "Cash collected successfully", "parcel_id": str(parcel_id)}


@router.post("/chapa/initiate")
async def initiate_chapa_payment(request: ChapaInitRequest, db: AsyncSession = Depends(get_db)):
    # Resolve the parcel by UUID (dashboard) or tracking code (Telegram bot).
    if request.parcel_id:
        parcel = await db.get(Parcel, request.parcel_id)
    elif request.tracking_code:
        parcel = (await db.execute(
            select(Parcel).where(Parcel.tracking_code == request.tracking_code.upper())
        )).scalar_one_or_none()
    else:
        raise HTTPException(status_code=422, detail="parcel_id or tracking_code required")
    if not parcel:
        raise NotFoundError("Parcel not found")

    sender = await db.get(Customer, parcel.sender_id)
    tx_ref = chapa.new_tx_ref(parcel.id)

    payment = Payment(
        parcel_id=parcel.id,
        amount=parcel.price,
        method=PaymentMethod.CHAPA,
        status=PaymentStatus.PENDING,
        chapa_tx_ref=tx_ref
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # No Chapa credentials configured.
    if not settings.chapa_secret_key:
        if settings.environment == "production":
            raise HTTPException(status_code=503, detail="Payment provider not configured")
        # Dev stub: confirm instantly so the whole bot flow is testable locally.
        payment.status = PaymentStatus.PAID
        payment.override_reason = "DEV MODE: no Chapa key configured — auto-confirmed"
        payment.verified_at = datetime.now(timezone.utc)
        parcel.payment_status = PaymentStatus.PAID
        await db.commit()
        return {"checkout_url": None, "dev_confirmed": True,
                "tracking_code": parcel.tracking_code, "tx_ref": tx_ref}

    checkout_url = await chapa.initiate_checkout(
        amount=float(parcel.price),
        tx_ref=tx_ref,
        customer_email=request.customer_email or f"{sender.phone if sender else 'customer'}@mela-express.placeholder",
        customer_phone=sender.phone if sender else "+251900000000",
        return_url="https://t.me/YourMelaExpressBot"
    )

    return {"checkout_url": checkout_url, "tx_ref": tx_ref}


@router.post("/chapa/webhook")
async def chapa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("Chapa-Signature", "")
    
    if not chapa.verify_webhook_signature(raw_body, signature):
        raise HTTPException(401, "Invalid webhook signature")
        
    payload = await request.json()
    tx_ref = payload.get("tx_ref")
    if not tx_ref:
        raise HTTPException(400, "Missing tx_ref")
        
    result = await db.execute(select(Payment).where(Payment.chapa_tx_ref == tx_ref))
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(404, "Unknown transaction reference")
        
    if payment.status == PaymentStatus.PAID:
        return {"status": "success", "note": "already processed"}
        
    verified = await chapa.verify_transaction(tx_ref)
    if verified.get("status") != "success":
        payment.status = PaymentStatus.FAILED
        await db.commit()
        return {"status": "failed"}
        
    payment.status = PaymentStatus.PAID
    payment.verified_at = datetime.now(timezone.utc)
    
    parcel = await db.get(Parcel, payment.parcel_id)
    if parcel:
        parcel.payment_status = PaymentStatus.PAID
        parcel.payment_method = PaymentMethod.CHAPA
        await db.commit()
        
        sender = await db.get(Customer, parcel.sender_id)
        await notify_payment_confirmed(
            db=db,
            customer_id=parcel.sender_id,
            phone=sender.phone if sender else None,
            telegram_id=sender.telegram_id if sender else None,
            tracking_code=parcel.tracking_code,
            amount=float(payment.amount),
            parcel_id=parcel.id
        )
        
    return {"status": "success"}
