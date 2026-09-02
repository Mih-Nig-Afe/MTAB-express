"""Central branding — all display names and tracking prefix from env only."""
import re
from functools import lru_cache

from app.config import settings


@lru_cache
def brand_name() -> str:
    return (settings.brand_name or settings.brand_short or "").strip()


@lru_cache
def brand_short() -> str:
    return settings.brand_short.strip()


@lru_cache
def tracking_prefix() -> str:
    raw = (settings.tracking_prefix or settings.brand_short or "").strip()
    return raw.upper()


def tracking_example(branch: str = "HW", serial: str = "000482") -> str:
    prefix = tracking_prefix()
    if not prefix:
        return ""
    return f"{prefix}-{branch}-{serial}"


def brand_context() -> dict[str, str]:
    prefix = tracking_prefix()
    return {
        "brand_name": brand_name(),
        "brand_short": brand_short(),
        "tracking_prefix": prefix,
        "tracking_example": tracking_example(),
    }


def tracking_code_pattern() -> str:
    """Regex for branch-suffix codes, e.g. {PREFIX}-HW-000482."""
    prefix = tracking_prefix()
    if not prefix:
        return r"\b([A-Z]{2,}-[A-Z0-9]{2,}-\d+)\b"
    return rf"\b({re.escape(prefix)}-[A-Z0-9]{{2,}}-\d+)\b"


def sms_sender_id() -> str:
    if settings.sms_sender_id:
        return settings.sms_sender_id
    short = brand_short()
    return f"{short}Express" if short else ""
