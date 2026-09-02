import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.api_client import api_base_url
from app.bot.helpers import resolve_lang
from app.bot.messages import msg

logger = logging.getLogger(__name__)


async def handle_pickup_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await resolve_lang(context, str(update.effective_user.id))
    tracking_code = query.data.split("_", 1)[1]
    telegram_id = str(update.effective_user.id)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{api_base_url()}/api/customers/telegram/{telegram_id}/pickup-code/{tracking_code}"
            )
            if response.status_code >= 400:
                detail = response.json().get("detail", msg(lang, "bot.error_generic"))
                await query.message.reply_text(f"⚠️ {detail}")
                return
            data = response.json()

        await query.message.reply_text(
            msg(
                lang,
                "bot.pickup_code",
                code=data["tracking_code"],
                otp=data["pickup_code"],
                branch=data.get("branch_name", ""),
            ),
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Error fetching pickup code")
        await query.message.reply_text(msg(lang, "bot.error_generic"))
