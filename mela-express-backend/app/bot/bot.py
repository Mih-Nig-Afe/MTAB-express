"""
Telegram bot for customers (senders/receivers). Deliberately thin: every
handler calls the backend API rather than touching the database directly.
This is the same lesson from Wiz Aroma's distributed bot architecture —
the bot is one client among several (web dashboard, future SMS gateway),
not where business logic lives.

Run separately from the API process: `python -m app.bot.bot`
"""
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.config import settings

API_BASE = settings.app_base_url  # backend API, not Chapa


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1 of the registration flow: ask for a phone number to link this Telegram ID."""
    keyboard = [[InlineKeyboardButton("Share my phone number", request_contact=True)]]
    await update.message.reply_text(
        "Welcome to Mela Express. Share your phone number to link your account "
        "and start receiving parcel updates here.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: link phone number to Telegram ID via the backend."""
    contact = update.message.contact
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/api/customers/link", json={
            "phone": contact.phone_number,
            "telegram_id": str(update.effective_user.id),
        })
    await update.message.reply_text(
        "You're linked. You'll get a message here every time one of your parcels changes status. "
        "Use /track <code> anytime to check a specific parcel."
    )


async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/track MEX-HW-4821 — on-demand status lookup."""
    if not context.args:
        await update.message.reply_text("Usage: /track MEX-HW-4821")
        return

    tracking_code = context.args[0].upper()
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/api/parcels/track/{tracking_code}")

    if resp.status_code == 404:
        await update.message.reply_text(f"No parcel found with code {tracking_code}.")
        return

    parcel = resp.json()
    text = (
        f"Parcel {parcel['tracking_code']}\n"
        f"Status: {parcel['status'].replace('_', ' ').title()}\n"
        f"Payment: {parcel['payment_status'].title()}"
    )

    if parcel["payment_status"] == "pending":
        keyboard = [[InlineKeyboardButton(
            "Pay now", callback_data=f"pay:{parcel['id']}"
        )]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text)


async def handle_pay_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for the inline 'Pay now' button — this is where diagram 2 starts."""
    query = update.callback_query
    await query.answer()
    parcel_id = query.data.split(":", 1)[1]

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/api/payments/chapa/initiate", json={
            "parcel_id": parcel_id,
        })
    data = resp.json()
    keyboard = [[InlineKeyboardButton("Open Chapa checkout", url=data["checkout_url"])]]
    await query.message.reply_text(
        "Tap below to complete payment securely via Chapa. "
        "You'll get a confirmation message here once it's processed.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def build_app() -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("track", track))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    # callback query handler for the pay button would be registered here too:
    # application.add_handler(CallbackQueryHandler(handle_pay_button, pattern=r"^pay:"))
    return application


if __name__ == "__main__":
    build_app().run_polling()
