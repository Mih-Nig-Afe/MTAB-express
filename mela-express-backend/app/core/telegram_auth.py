"""Validate Telegram WebApp initData (HMAC-SHA256)."""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from app.config import settings


def validate_telegram_init_data(init_data: str) -> dict | None:
    """Return parsed user payload if signature is valid, else None."""
    if not init_data or not settings.telegram_bot_token:
        return None

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        return None

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.encode(),
        hashlib.sha256,
    ).digest()
    computed = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        return None

    user_raw = data.get("user")
    if user_raw:
        try:
            data["user"] = json.loads(user_raw)
        except json.JSONDecodeError:
            return None
    return data
