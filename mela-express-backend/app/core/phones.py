"""Canonical E.164-style normalization for Ethiopian phone numbers.

Every entry point (dashboard login, bot contact share, customer linking,
customer lookups) must funnel through this so DB comparisons always match.
"""


def normalize_phone(phone: str) -> str:
    """Normalize to +2519XXXXXXXX form."""
    cleaned = (phone or "").strip().replace(" ", "").replace("-", "")
    if not cleaned:
        return cleaned
    if cleaned.startswith("0"):
        return "+251" + cleaned[1:]
    elif cleaned.startswith("251"):
        return "+" + cleaned
    elif not cleaned.startswith("+"):
        return "+251" + cleaned
    return cleaned
