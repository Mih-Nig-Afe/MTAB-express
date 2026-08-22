import httpx
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from app.bot.messages import WELCOME, LINKED, ERROR_GENERIC

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        [KeyboardButton("📱 Link Phone Number", request_contact=True)],
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

    inline_keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Open Mela Mini App",
                web_app=WebAppInfo(url="http://localhost:3001/mini-app")
            )
        ],
        [
            InlineKeyboardButton("🔍 Track Parcel", callback_data="cmd_track"),
            InlineKeyboardButton("📦 My Orders", callback_data="cmd_my_parcels"),
        ],
        [
            InlineKeyboardButton("🏢 Branch Hubs", callback_data="cmd_branches"),
            InlineKeyboardButton("📞 Customer Support", url="https://t.me/mela_support"),
        ]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(WELCOME, reply_markup=reply_markup)
    await update.message.reply_text("✨ Or launch our interactive web app directly inside Telegram:", reply_markup=inline_markup)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        return

    phone = contact.phone_number
    if phone.startswith("+"):
        phone = phone[1:]

    context.user_data["phone"] = phone

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/customers/link",
                json={"phone": phone, "telegram_id": str(update.effective_user.id)}
            )
            response.raise_for_status()
        
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    "📦 View My Parcels & Active Shipments",
                    web_app=WebAppInfo(url="http://localhost:3001/mini-app")
                )
            ]
        ]
        await update.message.reply_text(
            f"✅ *Account Successfully Linked!* \nPhone: `{phone}`\n\nYou will now receive automatic real-time push notifications whenever your shipments move across hubs.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
    except Exception as e:
        print(f"Error linking account: {e}")
        await update.message.reply_text(ERROR_GENERIC)
