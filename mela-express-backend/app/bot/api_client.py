"""Resolve the API base URL for bot → backend calls."""
from app.config import settings


def api_base_url() -> str:
    """Inside Docker use internal_api_url (http://api:8000); on host use app_base_url."""
    base = settings.internal_api_url or settings.app_base_url
    return base.rstrip("/")
