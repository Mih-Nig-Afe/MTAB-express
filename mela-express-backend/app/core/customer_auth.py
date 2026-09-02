"""Customer session JWT helpers."""
from datetime import timedelta

from app.core.security import create_access_token, decode_token


def create_customer_token(customer_id: str, telegram_id: str | None = None) -> str:
    return create_access_token(
        {"sub": customer_id, "type": "customer", "telegram_id": telegram_id},
        expires_delta=timedelta(days=30),
    )


def decode_customer_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "customer":
        raise ValueError("Not a customer token")
    return payload
