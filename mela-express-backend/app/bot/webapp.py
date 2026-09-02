"""Shared Telegram keyboard helpers."""
import ipaddress
from urllib.parse import urlparse

from telegram import InlineKeyboardButton, WebAppInfo

from app.config import settings


def _is_publicly_reachable(url: str) -> bool:
    """Telegram rejects inline-button URLs that aren't publicly routable
    (localhost, LAN IPs) as well as non-https web-app URLs."""
    host = urlparse(url).hostname
    if not host:
        return False
    if host in ("localhost", "0.0.0.0") or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        return True  # regular domain name


def mini_app_button(text: str, path: str = "/mini-app") -> InlineKeyboardButton | None:
    """Build a button that opens the public portal.

    - https + public host → native Telegram Mini App button
    - public http(s) host  → regular URL button (opens browser)
    - localhost/LAN        → None (Telegram rejects those URLs entirely);
                             callers should omit the row
    """
    url = f"{settings.public_portal_url.rstrip('/')}{path}"
    if not _is_publicly_reachable(url):
        return None
    if url.startswith("https://"):
        return InlineKeyboardButton(text, web_app=WebAppInfo(url=url))
    return InlineKeyboardButton(text, url=url)


def compact_rows(rows: list) -> list[list]:
    """Drop None buttons, None rows, and rows left empty by them."""
    result = []
    for row in rows:
        if row is None:
            continue
        filtered = [b for b in row if b is not None]
        if filtered:
            result.append(filtered)
    return result
