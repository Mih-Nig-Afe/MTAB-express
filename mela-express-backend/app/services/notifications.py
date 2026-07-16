"""
Outbound notification helpers (Telegram + SMS fallback + Celery queuing).
"""
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import ParcelStatus, NotificationLog
from app.workers.notification_tasks import send_telegram_notification, send_sms_notification
from app.services.sms import send_sms as sms_service_send_sms

STATUS_MESSAGES = {
    ParcelStatus.RECEIVED_AT_ORIGIN: "Your parcel {code} has been received at {branch} and is being processed.",
    ParcelStatus.IN_TRANSIT: "Your parcel {code} is on its way to {branch}.",
    ParcelStatus.ARRIVED_AT_DESTINATION: "Your parcel {code} has arrived at {branch}.",
    ParcelStatus.READY_FOR_PICKUP: "Your parcel {code} is ready for pickup at {branch}.",
    ParcelStatus.DELIVERED: "Your parcel {code} has been delivered. Thank you for using Mela Express.",
    ParcelStatus.ON_HOLD: "Your parcel {code} is on hold: {note}",
    ParcelStatus.RETURNED: "Your parcel {code} is being returned to sender.",
}

async def send_telegram_message(telegram_id: str, text: str) -> None:
    if not telegram_id or not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": telegram_id, "text": text})
    except Exception:
        pass

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
                               note: str | None = None, parcel_id=None) -> None:
    if not to_status:
        return
    template = STATUS_MESSAGES.get(to_status)
    if not template:
        return
    text = template.format(code=tracking_code, branch=branch_name, note=note or "")
    
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

async def notify_payment_confirmed(*, db: AsyncSession | None = None, customer_id=None, phone: str | None = None, telegram_id: str | None = None, 
                                   tracking_code: str = "", amount: float = 0.0, parcel_id=None) -> None:
    text = f"Payment of {amount} ETB confirmed for parcel {tracking_code}. Thank you."
    
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
