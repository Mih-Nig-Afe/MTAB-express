import httpx
from celery import shared_task
from app.config import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_telegram_notification(self, chat_id: str, text: str, reply_markup: dict | None = None):
    """Sends a Telegram message using the bot token."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error(f"Telegram API failed: {exc}")
        # Retry with exponential backoff: 60, 120, 240 seconds
        delay = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=delay)

@shared_task(bind=True, max_retries=3)
def send_sms_notification(self, phone: str, text: str):
    """Sends an SMS message using the configured SMS gateway."""
    if not settings.sms_api_url:
        logger.warning("SMS API URL not configured. Skipping SMS notification.")
        return

    payload = {
        "to": phone,
        "message": text,
        "sender_id": settings.sms_sender_id
    }
    
    headers = {
        "Authorization": f"Bearer {settings.sms_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = httpx.post(settings.sms_api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error(f"SMS API failed: {exc}")
        # Retry with exponential backoff: 60, 120, 240 seconds
        delay = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=delay)
