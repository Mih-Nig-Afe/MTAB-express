import sys
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from app.core.config import settings

from app.bot.handlers.start import start, handle_contact
from app.bot.handlers.track import track
from app.bot.handlers.my_parcels import my_parcels
from app.bot.handlers.payment import handle_pay_button
from app.bot.handlers.receipt import handle_receipt

logger = logging.getLogger(__name__)

def build_app():
    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bot will not start.")
        sys.exit(0)

    app = ApplicationBuilder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("my_parcels", my_parcels))

    # Messages
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_pay_button, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(handle_receipt, pattern="^receipt_"))

    return app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = build_app()
    app.run_polling()
