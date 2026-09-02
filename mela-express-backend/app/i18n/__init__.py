"""Request-scoped localization (English / Amharic) + shared message templates.

Locale resolution order per request:
  1. ?lang= query parameter        (explicit, wins)
  2. Accept-Language header        (browser preference)
  3. fallback: "en"

The active locale lives in a ContextVar set by middleware (app.i18n.middleware),
so any schema computed-field or exception handler can call t() transparently.

bot.* / notify.* keys are consumed by the Telegram bot and notification
service with an explicit locale argument (per-customer preference), NOT the
request context — use t(key, lang="am") for those.
"""
import json
from contextvars import ContextVar

locale_ctx: ContextVar[str] = ContextVar("locale", default="en")

SUPPORTED = ("en", "am")
_DEFAULT = "en"

def _load(name: str) -> dict:
    p = pathlib.Path(__file__).parent / "locales" / f"{name}.json"
    return json.loads(p.read_text())

import pathlib  # noqa: E402
_TRANSLATIONS = {name: _load(name) for name in SUPPORTED}


def get_locale() -> str:
    loc = locale_ctx.get()
    return loc if loc in SUPPORTED else _DEFAULT


def resolve_locale(query_lang: str | None, accept_language: str | None) -> str:
    q = (query_lang or "").strip().lower()
    if q in SUPPORTED:
        return q
    al = (accept_language or "").strip().lower()
    if al.startswith("am") or ",am" in al:
        return "am"
    return _DEFAULT


def t(key: str, lang: str | None = None) -> str:
    """Translate a namespaced key. Uses request locale unless `lang` given."""
    loc = lang if lang in SUPPORTED else get_locale()
    return (
        _TRANSLATIONS.get(loc, {}).get(key)
        or _TRANSLATIONS[_DEFAULT].get(key)
        or key
    )


def terr(english_detail: str) -> str:
    """Translate a known English error detail; unknown strings pass through."""
    return t(f"error.{english_detail}") if english_detail else english_detail
