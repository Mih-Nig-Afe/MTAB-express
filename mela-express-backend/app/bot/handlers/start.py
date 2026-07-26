import httpx
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from app.bot.messages import WELCOME, LINKED, ERROR_GENERIC

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📱 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(WELCOME, reply_markup=reply_markup)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        return

    phone = contact.phone_number
    # Basic normalization if needed (e.g., removing +)
    if phone.startswith("+"):
        phone = phone[1:]

    context.user_data["phone"] = phone

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/customers/link",
                json={"phone": phone, "telegram_id": str(update.effective_user.id)}
            )
            response.raise_for_status()
        
        await update.message.reply_text(LINKED, reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        print(f"Error linking account: {e}")
        await update.message.reply_text(ERROR_GENERIC, reply_markup=ReplyKeyboardRemove())
