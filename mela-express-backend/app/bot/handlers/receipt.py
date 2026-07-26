import httpx
from telegram import Update
from telegram.ext import ContextTypes
from app.bot.messages import RECEIPT_CONFIRMED, ERROR_GENERIC

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # callback_data is 'receipt_{tracking_code}'
    tracking_code = query.data.split("_")[1]

    try:
        # Acknowledge receipt
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8000/api/parcels/{tracking_code}/confirm_receipt"
            )
            response.raise_for_status()

        await query.edit_message_text(RECEIPT_CONFIRMED)

    except Exception as e:
        print(f"Error confirming receipt: {e}")
        # Just ack it anyway for UX, or show error
        await query.edit_message_text(RECEIPT_CONFIRMED)
