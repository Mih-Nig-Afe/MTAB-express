from telegram import Update
from telegram.ext import ContextTypes

from app.bot.handlers.start import _main_menu
from app.bot.helpers import resolve_lang
from app.bot.messages import msg


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await resolve_lang(context, str(update.effective_user.id), update.effective_user.language_code)
    await update.message.reply_text(
        msg(lang, "bot.help_text"),
        parse_mode="Markdown",
        reply_markup=await _main_menu(lang),
    )
