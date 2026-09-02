import logging

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.messages import msg
from app.bot.api_client import api_base_url
from app.bot.helpers import resolve_lang

logger = logging.getLogger(__name__)


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await resolve_lang(context, str(update.effective_user.id))

    # callback_data is 'receipt_{tracking_code}'
    tracking_code = query.data.split("_", 1)[1]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{api_base_url()}/api/parcels/track/{tracking_code}/confirm_receipt"
            )
            if response.status_code >= 400:
                detail = response.json().get("detail") or msg(lang, "bot.error_generic")
                await query.edit_message_text(f"⚠️ {detail}")
                return
            response.raise_for_status()

        await query.edit_message_text(msg(lang, "bot.receipt_confirmed"))

    except Exception:
        logger.exception("Error confirming receipt")
        await query.edit_message_text(msg(lang, "bot.error_generic"))
