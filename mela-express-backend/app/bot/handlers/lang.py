"""/lang — switch message language (am | en) and persist to the customer profile."""
import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.messages import msg
from app.bot.api_client import api_base_url

logger = logging.getLogger(__name__)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_arg = (context.args[0].lower() if context.args else "")
    if lang_arg not in ("am", "en"):
        await update.message.reply_text("Usage: /lang am  |  /lang en")
        return

    # Apply immediately (session), then persist to the customer profile.
    context.user_data["lang"] = lang_arg

    telegram_id = str(update.effective_user.id)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{api_base_url()}/api/customers/language",
                json={"telegram_id": telegram_id, "language": lang_arg},
            )
    except Exception:
        logger.exception("Failed to persist language preference")

    await update.message.reply_text(msg(lang_arg, f"bot.lang_changed_{lang_arg}"))
