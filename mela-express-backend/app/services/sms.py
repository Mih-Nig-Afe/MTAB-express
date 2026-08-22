import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def send_sms(phone: str, message: str) -> bool:
    """Sends SMS via the configured gateway."""
    if not settings.sms_api_url:
        logger.warning("SMS API URL not configured. Skipping SMS.")
        return False

    payload = {
        "to": phone,
        "message": message,
        "sender_id": settings.sms_sender_id
    }
    
    headers = {
        "Authorization": f"Bearer {settings.sms_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(settings.sms_api_url, json=payload, headers=headers)
            response.raise_for_status()
            return True
    except httpx.HTTPError as exc:
        logger.error(f"Failed to send SMS to {phone}: {exc}")
        return False
