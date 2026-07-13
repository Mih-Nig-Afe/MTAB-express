"""
Thin wrapper around the Telegram Bot API for outbound notifications.
Called from routers after a status or payment change commits — never called
mid-transaction, so a slow/failed Telegram call never blocks a DB write.
In production, push these onto a queue (Celery/arq) instead of awaiting inline.
"""
import httpx

from app.config import settings
from app.models import ParcelStatus

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
    if not telegram_id:
        return  # customer hasn't linked Telegram yet — fall back to SMS in a real deployment
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": telegram_id, "text": text})


async def notify_status_change(*, telegram_id: str, tracking_code: str, branch_name: str,
                                to_status: ParcelStatus, note: str | None = None) -> None:
    template = STATUS_MESSAGES.get(to_status)
    if not template:
        return
    text = template.format(code=tracking_code, branch=branch_name, note=note or "")
    await send_telegram_message(telegram_id, text)


async def notify_payment_confirmed(*, telegram_id: str, tracking_code: str, amount: float) -> None:
    text = f"Payment of {amount} ETB confirmed for parcel {tracking_code}. Thank you."
    await send_telegram_message(telegram_id, text)
