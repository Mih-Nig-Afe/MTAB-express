"""
Chapa integration. Two responsibilities only:
  1. initiate_checkout()  — ask Chapa for a hosted payment link, hand it to the bot.
  2. verify_transaction() — never trust a webhook payload alone; call Chapa back
     to confirm the transaction actually succeeded before touching our DB.

Docs: https://developer.chapa.co — re-check field/header names against the
current docs before going live, payment provider APIs shift over time.
"""
import hashlib
import hmac
import uuid

import httpx

from app.config import settings


class ChapaError(Exception):
    pass


async def initiate_checkout(
    *,
    amount: float,
    tx_ref: str,
    customer_email: str,
    customer_phone: str,
    return_url: str,
) -> str:
    """Returns the hosted checkout URL to send the customer to via the Telegram bot."""
    headers = {"Authorization": f"Bearer {settings.chapa_secret_key}"}
    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "tx_ref": tx_ref,
        "phone_number": customer_phone,
        "email": customer_email,
        "callback_url": f"{settings.app_base_url}/api/payments/chapa/webhook",
        "return_url": return_url,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.chapa_base_url}/transaction/initialize",
            json=payload,
            headers=headers,
        )
    data = resp.json()
    if data.get("status") != "success":
        raise ChapaError(f"Chapa checkout init failed: {data}")
    return data["data"]["checkout_url"]


async def verify_transaction(tx_ref: str) -> dict:
    """
    Server-to-server verification call. This is the step that actually decides
    whether a payment is real — the webhook alone is not sufficient authority.
    """
    headers = {"Authorization": f"Bearer {settings.chapa_secret_key}"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.chapa_base_url}/transaction/verify/{tx_ref}",
            headers=headers,
        )
    data = resp.json()
    if data.get("status") != "success":
        raise ChapaError(f"Chapa verification failed for {tx_ref}: {data}")
    return data["data"]  # contains amount, status ("success"/"failed"), currency, etc.


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Confirms the webhook actually came from Chapa before we even look at its
    contents. Uses constant-time comparison to avoid timing attacks.
    Check Chapa's current docs for the exact header name and hashing scheme —
    this assumes an HMAC-SHA256 signature, which is the common pattern.
    """
    if not signature_header or not settings.chapa_webhook_secret:
        return False
    computed = hmac.new(
        settings.chapa_webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, signature_header)


def new_tx_ref(parcel_id: uuid.UUID) -> str:
    """Unique, non-guessable transaction reference tied to the parcel."""
    return f"mela-{parcel_id}-{uuid.uuid4().hex[:8]}"
