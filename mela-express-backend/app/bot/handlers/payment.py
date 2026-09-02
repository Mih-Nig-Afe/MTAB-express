import logging
import httpx
logger = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.messages import msg
from app.bot.api_client import api_base_url
from app.bot.helpers import resolve_lang

async def handle_pay_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # callback_data is 'pay_{tracking_code}'
    tracking_code = query.data.split("_", 1)[1]

    lang = await resolve_lang(context, str(update.effective_user.id))
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{api_base_url()}/api/payments/chapa/initiate",
                json={"tracking_code": tracking_code}
            )
            if response.status_code >= 400:
                detail = response.json().get("detail", "Payment failed.")
                await query.edit_message_text(f"⚠️ {detail}")
                return
            response.raise_for_status()
            data = response.json()

        if data.get("dev_confirmed"):
            await query.edit_message_text(
                msg(lang, "bot.payment_dev_confirmed", code=data["tracking_code"]),
                parse_mode="Markdown",
            )
            return

        checkout_url = data.get("checkout_url")
        if checkout_url:
            keyboard = [[InlineKeyboardButton("🔗 Proceed to Chapa", url=checkout_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(msg(lang, "bot.payment_initiated"), reply_markup=reply_markup)
        else:
            await query.edit_message_text("Payment initiation failed. No checkout URL returned.")

    except Exception as e:
        logger.exception("Error initiating payment")
        await query.edit_message_text(msg(lang, "bot.error_generic"))
