import logging
import httpx
logger = logging.getLogger(__name__)

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.bot.messages import msg
from app.bot.webapp import mini_app_button, compact_rows
from app.bot.api_client import api_base_url
from app.bot.helpers import resolve_lang, fetch_customer_by_telegram
from app.core.phones import normalize_phone
from app.core.brand import telegram_support_url


async def _main_menu(lang: str) -> InlineKeyboardMarkup:
    support = telegram_support_url()
    support_row = []
    if support:
        support_row.append(
            InlineKeyboardButton("📞 Customer Support" if lang == "en" else "📞 ድጋፍ", url=support)
        )
    inline_keyboard = compact_rows([
        [mini_app_button(msg(lang, "bot.mini_app_open"))],
        [
            InlineKeyboardButton("🔍 Track Parcel" if lang == "en" else "🔍 እቃ መከታተል", callback_data="cmd_track"),
            InlineKeyboardButton("📦 My Orders" if lang == "en" else "📦 የእኔ ትዕዛዞች", callback_data="cmd_my_parcels"),
        ],
        [
            InlineKeyboardButton("🏢 Branch Hubs" if lang == "en" else "🏢 ቅርንጫፎች", callback_data="cmd_branches"),
            *support_row,
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard) if inline_keyboard else InlineKeyboardMarkup([])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    lang = await resolve_lang(context, telegram_id, update.effective_user.language_code)
    customer = await fetch_customer_by_telegram(telegram_id)
    inline_markup = await _main_menu(lang)

    if customer and customer.get("phone"):
        await update.message.reply_text(
            msg(lang, "bot.welcome_back", name=update.effective_user.first_name or ""),
            parse_mode="Markdown",
            reply_markup=inline_markup,
        )
        return

    reply_keyboard = [[KeyboardButton("📱 Link Phone Number" if lang == "en" else "📱 ስልክ ያጋሩ", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(msg(lang, "bot.welcome"), reply_markup=reply_markup)
    await update.message.reply_text(msg(lang, "bot.mini_app_teaser"), reply_markup=inline_markup)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        return

    phone = normalize_phone(contact.phone_number)
    context.user_data["phone"] = phone
    lang = context.user_data.get("lang", "en")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{api_base_url()}/api/customers/link",
                json={"phone": phone, "telegram_id": str(update.effective_user.id)},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("language") in ("en", "am"):
                lang = data["language"]
                context.user_data["lang"] = lang

        btn = mini_app_button("📦 View My Parcels & Active Shipments" if lang == "en" else "📦 እቃዎቼ")
        markup = InlineKeyboardMarkup([[btn]]) if btn else None
        await update.message.reply_text(
            msg(lang, "bot.link_success", phone=phone),
            parse_mode="Markdown",
            reply_markup=markup,
        )
        await update.message.reply_text(msg(lang, "bot.link_done_hint"), reply_markup=await _main_menu(lang))
    except Exception:
        logger.exception("Error linking account")
        await update.message.reply_text(msg(lang, "bot.error_generic"))
