import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.messages import PAYMENT_CONFIRMED, ERROR_GENERIC

async def handle_pay_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # callback_data is 'pay_{tracking_code}'
    tracking_code = query.data.split("_")[1]
    phone = context.user_data.get("phone", "000000000") # Fallback if not logged in

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/payments/chapa/initiate",
                json={
                    "parcel_id": tracking_code, # Assuming backend accepts tracking_code or we can pass it
                    "amount": 100, # Hardcoded or dynamic? Backend should ideally know
                    "phone": phone
                }
            )
            response.raise_for_status()
            data = response.json()

        checkout_url = data.get("checkout_url")
        if checkout_url:
            keyboard = [[InlineKeyboardButton("🔗 Proceed to Chapa", url=checkout_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(PAYMENT_CONFIRMED, reply_markup=reply_markup)
        else:
            await query.edit_message_text("Payment initiation failed. No checkout URL returned.")

    except Exception as e:
        print(f"Error initiating payment: {e}")
        await query.edit_message_text(ERROR_GENERIC)
