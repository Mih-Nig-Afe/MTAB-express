import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Parcel, Payment, PaymentMethod, PaymentStatus, Customer
from app.schemas import ChapaInitRequest
from app.services import chapa
from app.services.notifications import notify_payment_confirmed

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/cash/{parcel_id}/collect")
async def mark_cash_collected(parcel_id: uuid.UUID, collected_by: uuid.UUID,
                               reason: str | None = None, db: AsyncSession = Depends(get_db)):
    """
    Manual cash collection. `reason` is required-in-spirit whenever this is used
    to override a normally-online flow — surface it in admin reports so patterns
    of manual overrides by a given operator are visible, not buried.
    """
    parcel = await db.get(Parcel, parcel_id)
    if parcel is None:
        raise HTTPException(404, "Parcel not found")

    payment = Payment(
        parcel_id=parcel.id, amount=parcel.price, method=PaymentMethod.CASH,
        status=PaymentStatus.PAID, collected_by=collected_by,
    )
    db.add(payment)
    parcel.payment_status = PaymentStatus.PAID
    parcel.payment_method = PaymentMethod.CASH
    await db.commit()
    return {"ok": True, "parcel_id": str(parcel_id), "reason": reason}


@router.post("/chapa/initiate")
async def initiate_chapa_payment(payload: ChapaInitRequest, db: AsyncSession = Depends(get_db)):
    """Called by the Telegram bot when the customer taps 'Pay now'."""
    parcel = await db.get(Parcel, payload.parcel_id)
    if parcel is None:
        raise HTTPException(404, "Parcel not found")

    sender = await db.get(Customer, parcel.sender_id)
    tx_ref = chapa.new_tx_ref(parcel.id)

    payment = Payment(
        parcel_id=parcel.id, amount=parcel.price, method=PaymentMethod.CHAPA,
        chapa_tx_ref=tx_ref, status=PaymentStatus.PENDING,
    )
    db.add(payment)
    await db.commit()

    checkout_url = await chapa.initiate_checkout(
        amount=float(parcel.price),
        tx_ref=tx_ref,
        customer_email=payload.customer_email or f"{sender.phone}@mela-express.placeholder",
        customer_phone=sender.phone,
        return_url=f"https://t.me/YourMelaExpressBot",  # bounce back to the bot after checkout
    )
    return {"checkout_url": checkout_url, "tx_ref": tx_ref}


@router.post("/chapa/webhook")
async def chapa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Chapa calls this after a payment attempt. We do NOT trust this payload on
    its own — verify the signature, then call Chapa's verify endpoint as the
    actual source of truth before marking anything paid.

    Idempotency: chapa_tx_ref is unique on the Payment row and we check current
    status before acting, so a duplicate/retried webhook is a safe no-op.
    """
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
    if payment is None:
        raise HTTPException(404, "Unknown transaction reference")

    if payment.status == PaymentStatus.PAID:
        return {"ok": True, "note": "already processed, idempotent no-op"}

    # source of truth: ask Chapa directly, don't trust the webhook body alone
    verified = await chapa.verify_transaction(tx_ref)

    if verified.get("status") != "success":
        payment.status = PaymentStatus.FAILED
        await db.commit()
        return {"ok": True, "note": "payment not successful"}

    payment.status = PaymentStatus.PAID
    from datetime import datetime, timezone
    payment.verified_at = datetime.now(timezone.utc)

    parcel = await db.get(Parcel, payment.parcel_id)
    parcel.payment_status = PaymentStatus.PAID
    parcel.payment_method = PaymentMethod.CHAPA
    await db.commit()

    sender = await db.get(Customer, parcel.sender_id)
    if sender and sender.telegram_id:
        await notify_payment_confirmed(
            telegram_id=sender.telegram_id, tracking_code=parcel.tracking_code,
            amount=float(payment.amount),
        )
    return {"ok": True}
