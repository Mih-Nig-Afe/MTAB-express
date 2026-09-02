import logging
import httpx

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.bot.messages import msg
from app.i18n import t
from app.bot.webapp import mini_app_button
from app.bot.api_client import api_base_url
from app.bot.helpers import resolve_lang

logger = logging.getLogger(__name__)


async def send_my_parcels(message, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(message.chat.id)
    lang = await resolve_lang(context, telegram_id)
    phone = context.user_data.get("phone")
    if not phone:
        from app.bot.helpers import fetch_customer_by_telegram
        customer = await fetch_customer_by_telegram(telegram_id)
        if customer:
            phone = customer.get("phone")
            context.user_data["phone"] = phone
    if not phone:
        await message.reply_text(msg(lang, "bot.link_prompt"))
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{api_base_url()}/api/customers/me/parcels?phone={phone}")
            response.raise_for_status()
            parcels = response.json()

        btn = mini_app_button(msg(lang, "bot.mini_app_open"))
        keyboard = InlineKeyboardMarkup([[btn]]) if btn else None

        if not parcels:
            await message.reply_text(msg(lang, "bot.my_parcels_empty"), reply_markup=keyboard)
            return

        active_parcels = [p for p in parcels if p["status"] not in ["delivered", "cancelled", "returned", "lost"]]
        completed_parcels = [p for p in parcels if p["status"] in ["delivered", "cancelled", "returned", "lost"]]

        text = msg(lang, "bot.my_parcels_header")

        if active_parcels:
            text += msg(lang, "bot.active") + "\n"
            for p in active_parcels:
                st = t(f"parcel_status.{p['status']}", lang=lang)
                text += msg(lang, "bot.my_parcels_item", code=p["tracking_code"], status=st) + "\n"
            text += "\n"

        if completed_parcels:
            text += msg(lang, "bot.completed") + "\n"
            for p in completed_parcels:
                st = t(f"parcel_status.{p['status']}", lang=lang)
                text += msg(lang, "bot.my_parcels_item", code=p["tracking_code"], status=st) + "\n"

        await message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception:
        logger.exception("Error fetching parcels")
        await message.reply_text(msg(lang, "bot.error_generic"))


async def my_parcels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_my_parcels(update.message, context)


async def handle_branches(message, context: ContextTypes.DEFAULT_TYPE = None):
    lang = "en"
    if context:
        lang = await resolve_lang(context, str(message.chat.id))
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{api_base_url()}/api/branches/public")
            response.raise_for_status()
            branches = response.json()

        lines = [msg(lang, "bot.branches_header")]
        for b in branches:
            city = f" — {b['city']}" if b.get("city") else ""
            phone = f"\n   ☎ {b['phone']}" if b.get("phone") else ""
            lines.append(f"• *{b['name']}*{city}{phone}")
        await message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception:
        logger.exception("Error fetching branches")
        await message.reply_text(msg(lang, "bot.error_generic"))


async def handle_menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data
    await query.answer()
    lang = await resolve_lang(context, str(update.effective_user.id), update.effective_user.language_code)

    if action == "cmd_track":
        await query.message.reply_text(msg(lang, "bot.track_usage"))
    elif action == "cmd_my_parcels":
        await send_my_parcels(query.message, context)
    elif action == "cmd_branches":
        await handle_branches(query.message, context)
