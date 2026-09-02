"""Bot message templates, localized per customer preferred language."""
from app.i18n import t


def msg(lang: str, key: str, **fmt) -> str:
    text = t(key, lang=lang)
    return text.format(**fmt) if fmt else text


def lang_for(telegram_lang: str | None) -> str:
    return "am" if (telegram_lang or "").lower().startswith("am") else "en"
