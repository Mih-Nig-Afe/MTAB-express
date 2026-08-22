import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.messages import TRACK_USAGE, PARCEL_NOT_FOUND, STATUS_FORMAT, ERROR_GENERIC

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(TRACK_USAGE)
        return

    code = context.args[0].upper()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/parcels/track/{code}")
            
            if response.status_code == 404:
                await update.message.reply_text(PARCEL_NOT_FOUND.format(code=code))
                return
            
            response.raise_for_status()
            data = response.json()

        status_text = STATUS_FORMAT.format(
            code=data["tracking_code"],
            origin=data["origin_branch_name"],
            destination=data["destination_branch_name"],
            status=data["status"],
            payment_status=data["payment_status"]
        )

        reply_markup = None
        if data["payment_status"] == "pending":
            keyboard = [[InlineKeyboardButton("💳 Pay Now", callback_data=f"pay_{data['tracking_code']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(status_text, parse_mode="Markdown", reply_markup=reply_markup)

    except Exception as e:
        print(f"Error tracking parcel: {e}")
        await update.message.reply_text(ERROR_GENERIC)
