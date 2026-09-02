"""
Outbound notification helpers (Telegram + SMS fallback + Celery queuing).
"""
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import ParcelStatus, NotificationLog
from app.workers.notification_tasks import send_telegram_notification, send_sms_notification
from app.services.sms import send_sms as sms_service_send_sms


@dataclass
class NotifyTarget:
    role: str  # sender | receiver
    channel: str  # telegram | sms
    address: str
    customer_id: object | None = None


def resolve_notify_targets(*, sender, receiver, receiver_phone: str | None = None) -> list[NotifyTarget]:
    """One channel per party: Telegram if linked, otherwise SMS."""
    targets: list[NotifyTarget] = []

    if sender is not None:
        if getattr(sender, "telegram_id", None):
            targets.append(NotifyTarget("sender", "telegram", sender.telegram_id, getattr(sender, "id", None)))
        elif getattr(sender, "phone", None):
            targets.append(NotifyTarget("sender", "sms", sender.phone, getattr(sender, "id", None)))

    recv_telegram = getattr(receiver, "telegram_id", None) if receiver is not None else None
    recv_phone = getattr(receiver, "phone", None) if receiver is not None else None
    phone = recv_phone or receiver_phone
    recv_id = getattr(receiver, "id", None) if receiver is not None else None
    if recv_telegram:
        targets.append(NotifyTarget("receiver", "telegram", recv_telegram, recv_id))
    elif phone:
        targets.append(NotifyTarget("receiver", "sms", phone, recv_id))

    return targets

def _status_text(status: ParcelStatus, lang: str) -> str:
    from app.i18n import t
    return t(f"notify.status.{status.value}", lang=lang)

async def _customer_language(db: AsyncSession | None, customer_id) -> str:
    """Resolve the recipient's preferred language ('en' fallback)."""
    if not db or not customer_id:
        return "en"
    try:
        from sqlalchemy.ext.asyncio import AsyncSession as _S  # typing only
        from app.models import Customer
        cust = await db.get(Customer, customer_id)
        return getattr(cust, "language", None) or "en"
    except Exception:
        return "en"

async def send_telegram_message(telegram_id: str, text: str, reply_markup: dict | None = None) -> None:
    if not telegram_id or not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload: dict = {"chat_id": telegram_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
    except Exception:
        pass


def build_status_reply_markup(
    *,
    tracking_code: str,
    status: str,
    payment_status: str,
) -> dict | None:
    portal = settings.public_portal_url.rstrip("/")
    rows: list[list[dict]] = []
    rows.append([{"text": "📍 Track Live", "url": f"{portal}/track/{tracking_code}"}])
    if payment_status == "pending":
        rows.append([{"text": "💳 Pay Now", "callback_data": f"pay_{tracking_code}"}])
    if status == "ready_for_pickup":
        rows.append([{"text": "🔑 Pickup Code", "callback_data": f"pickup_{tracking_code}"}])
    if status == "delivered":
        rows.append([{"text": "✅ Confirm Receipt", "callback_data": f"receipt_{tracking_code}"}])
    return {"inline_keyboard": rows} if rows else None

async def send_sms(phone: str, message: str) -> bool:
    return await sms_service_send_sms(phone, message)

async def log_notification(db: AsyncSession | None, parcel_id, customer_id, channel, message, status):
    if not db:
        return
    try:
        log_entry = NotificationLog(
            parcel_id=parcel_id,
            customer_id=customer_id,
            channel=channel,
            message=message,
            status=status
        )
        db.add(log_entry)
        await db.commit()
    except Exception:
        pass

async def notify_status_change(*, db: AsyncSession | None = None, customer_id=None, phone: str | None = None, telegram_id: str | None = None, 
                               tracking_code: str = "", branch_name: str = "", to_status: ParcelStatus | None = None, 
                               note: str | None = None, parcel_id=None, payment_status: str = "pending") -> None:
    if not to_status:
        return
    lang = await _customer_language(db, customer_id)
    text = _status_text(to_status, lang).format(code=tracking_code, branch=branch_name, note=note or "")
    markup = build_status_reply_markup(
        tracking_code=tracking_code,
        status=to_status.value,
        payment_status=payment_status,
    )
    
    if telegram_id:
        try:
            send_telegram_notification.delay(telegram_id, text, markup)
        except Exception:
            await send_telegram_message(telegram_id, text, markup)
        await log_notification(db, parcel_id, customer_id, "telegram", text, "sent")
    elif phone:
        try:
            send_sms_notification.delay(phone, text)
        except Exception:
            await send_sms(phone, text)
        await log_notification(db, parcel_id, customer_id, "sms", text, "sent")

async def notify_parcel_parties(
    *,
    db: AsyncSession | None = None,
    sender=None,
    receiver=None,
    receiver_phone: str | None = None,
    tracking_code: str = "",
    branch_name: str = "",
    to_status: ParcelStatus | None = None,
    note: str | None = None,
    parcel_id=None,
    message: str | None = None,
    payment_status: str = "pending",
) -> list[NotifyTarget]:
    """Notify both sender and receiver of a status change or pickup reminder."""
    targets = resolve_notify_targets(
        sender=sender, receiver=receiver, receiver_phone=receiver_phone
    )
    if not targets:
        return []
    for target in targets:
        if message:
            text = message
            if target.channel == "telegram":
                try:
                    send_telegram_notification.delay(target.address, text)
                except Exception:
                    await send_telegram_message(target.address, text)
            else:
                try:
                    send_sms_notification.delay(target.address, text)
                except Exception:
                    await send_sms(target.address, text)
            await log_notification(db, parcel_id, target.customer_id, target.channel, text, "sent")
            continue
        if not to_status:
            continue
        await notify_status_change(
            db=db,
            customer_id=target.customer_id,
            phone=target.address if target.channel == "sms" else None,
            telegram_id=target.address if target.channel == "telegram" else None,
            tracking_code=tracking_code,
            branch_name=branch_name,
            to_status=to_status,
            note=note,
            parcel_id=parcel_id,
            payment_status=payment_status,
        )
    return targets


async def notify_payment_confirmed(*, db: AsyncSession | None = None, customer_id=None, phone: str | None = None, telegram_id: str | None = None, 
                                   tracking_code: str = "", amount: float = 0.0, parcel_id=None) -> None:
    lang = await _customer_language(db, customer_id)
    from app.i18n import t
    text = t("notify.payment_confirmed", lang=lang).format(amount=amount, tracking_code=tracking_code)
    
    if telegram_id:
        try:
            send_telegram_notification.delay(telegram_id, text)
        except Exception:
            await send_telegram_message(telegram_id, text)
        await log_notification(db, parcel_id, customer_id, "telegram", text, "sent")
    elif phone:
        try:
            send_sms_notification.delay(phone, text)
        except Exception:
            await send_sms(phone, text)
        await log_notification(db, parcel_id, customer_id, "sms", text, "sent")
