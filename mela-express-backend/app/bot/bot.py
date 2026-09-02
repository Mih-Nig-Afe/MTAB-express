import sys
import logging
from telegram import BotCommand, MenuButtonWebApp, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from app.config import settings

from app.bot.handlers.start import start, handle_contact
from app.bot.handlers.track import track
from app.bot.handlers.my_parcels import my_parcels, handle_menu_callbacks
from app.bot.handlers.lang import set_language
from app.bot.handlers.payment import handle_pay_button
from app.bot.handlers.receipt import handle_receipt
from app.bot.handlers.help import help_command
from app.bot.handlers.pickup import handle_pickup_button
from app.bot.handlers.messages import handle_text_message

logger = logging.getLogger(__name__)

def build_app():
    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bot will not start.")
        sys.exit(0)

    async def post_init(application):
        # Slash-command hints in the chat menu.
        await application.bot.set_my_commands([
            BotCommand("start", "Welcome & link your phone"),
            BotCommand("track", "Track a parcel, e.g. /track MEX-HW-000482"),
            BotCommand("my_parcels", "View your shipments"),
            BotCommand("help", "Commands & tips"),
            BotCommand("lang", "Switch language (en / am)"),
        ])
        # The ≡ menu button launches the Mini App directly — but Telegram only
        # accepts https web-app URLs there. Locally (http portal) we skip it;
        # in production this gives every user a one-tap entry point.
        portal = settings.public_portal_url.rstrip("/")
        if portal.startswith("https://"):
            try:
                await application.bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(
                        text="🚀 Open App",
                        web_app=WebAppInfo(url=f"{portal}/mini-app"),
                    )
                )
            except Exception as e:
                logger.warning("Could not set web-app menu button: %s", e)

    app = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("my_parcels", my_parcels))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lang", set_language))

    # Messages
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_menu_callbacks, pattern="^cmd_"))
    app.add_handler(CallbackQueryHandler(handle_pay_button, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(handle_pickup_button, pattern="^pickup_"))
    app.add_handler(CallbackQueryHandler(handle_receipt, pattern="^receipt_"))

    return app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = build_app()
    app.run_polling()
