import re

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.handlers.track import track_parcel_by_code

TRACKING_RE = re.compile(r"\b(MEX-[A-Z0-9]{2,}-\d+)\b", re.IGNORECASE)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    match = TRACKING_RE.search(update.message.text.strip())
    if not match:
        return
    code = match.group(1).upper()
    await track_parcel_by_code(update, context, code)
