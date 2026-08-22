import httpx
from telegram import Update
from telegram.ext import ContextTypes
from app.bot.messages import MY_PARCELS_HEADER, MY_PARCELS_EMPTY, MY_PARCELS_ITEM, ERROR_GENERIC

async def my_parcels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data.get("phone")
    if not phone:
        await update.message.reply_text("Please use /start and share your contact to link your account first.")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/customers/me/parcels?phone={phone}")
            response.raise_for_status()
            parcels = response.json()

        if not parcels:
            await update.message.reply_text(MY_PARCELS_EMPTY)
            return

        active_parcels = [p for p in parcels if p["status"] not in ["delivered", "cancelled", "failed"]]
        completed_parcels = [p for p in parcels if p["status"] in ["delivered", "cancelled", "failed"]]

        text = MY_PARCELS_HEADER + "\n"
        
        if active_parcels:
            text += "*Active:*\n"
            for p in active_parcels:
                text += MY_PARCELS_ITEM.format(code=p["tracking_code"], status=p["status"]) + "\n"
            text += "\n"
            
        if completed_parcels:
            text += "*Completed:*\n"
            for p in completed_parcels:
                text += MY_PARCELS_ITEM.format(code=p["tracking_code"], status=p["status"]) + "\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        print(f"Error fetching parcels: {e}")
        await update.message.reply_text(ERROR_GENERIC)
