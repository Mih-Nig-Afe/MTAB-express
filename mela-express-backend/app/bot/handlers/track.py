import logging
import httpx
logger = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.messages import msg
from app.i18n import t
from app.bot.webapp import mini_app_button, compact_rows
from app.bot.api_client import api_base_url
from app.bot.helpers import resolve_lang

async def track_parcel_by_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    lang = await resolve_lang(context, str(update.effective_user.id), update.effective_user.language_code)
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message:
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{api_base_url()}/api/parcels/track/{code}")
            
            if response.status_code == 404:
                await message.reply_text(msg(lang, "bot.parcel_not_found", code=code))
                return
            
            response.raise_for_status()
            data = response.json()

        status_text = msg(lang, "bot.status_format",
            code=data["tracking_code"],
            origin=data["origin_branch_name"],
            destination=data["destination_branch_name"],
            status=t(f"parcel_status.{data['status']}", lang=lang).upper(),
            payment_status=t(f"payment_status.{data['payment_status']}", lang=lang).upper(),
        )

        flight = data.get("flight")
        if flight and flight.get("flight_number"):
            status_text += msg(lang, "bot.flight_line",
                flight=flight["flight_number"],
                status=flight.get("status", "scheduled"),
            )

        buttons = compact_rows([
            [mini_app_button("📍 Live Timeline & Map" if lang == "en" else "📍 ቀጥታ መከታተያ", path=f"/track/{code}")],
            [InlineKeyboardButton("💳 Pay Online (Chapa)", callback_data=f"pay_{data['tracking_code']}")]
            if data["payment_status"] == "pending" else None,
            [InlineKeyboardButton("🔑 Pickup Code" if lang == "en" else "🔑 የመውሰድ ኮድ", callback_data=f"pickup_{data['tracking_code']}")]
            if data["status"] == "ready_for_pickup" else None,
            [InlineKeyboardButton("✅ Confirm Receipt", callback_data=f"receipt_{data['tracking_code']}")]
            if data["status"] == "delivered" else None,
        ])
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
        await message.reply_text(status_text, parse_mode="Markdown", reply_markup=reply_markup)

    except Exception:
        logger.exception("Error tracking parcel")
        await message.reply_text(msg(lang, "bot.error_generic"))


async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await resolve_lang(context, str(update.effective_user.id), update.effective_user.language_code)
    if not context.args:
        await update.message.reply_text(msg(lang, "bot.track_usage"))
        return
    await track_parcel_by_code(update, context, context.args[0].upper())
