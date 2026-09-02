"""Shared bot helpers — language resolution and customer lookup."""
from __future__ import annotations

import logging

import httpx
from telegram.ext import ContextTypes

from app.bot.api_client import api_base_url
from app.bot.messages import lang_for, msg

logger = logging.getLogger(__name__)


async def fetch_customer_by_telegram(telegram_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{api_base_url()}/api/customers/telegram/{telegram_id}")
            if response.status_code == 200:
                return response.json()
    except Exception:
        logger.exception("Failed to fetch customer by telegram_id")
    return None


async def resolve_lang(context: ContextTypes.DEFAULT_TYPE, telegram_id: str, telegram_lang: str | None = None) -> str:
    if context.user_data.get("lang") in ("en", "am"):
        return context.user_data["lang"]

    customer = await fetch_customer_by_telegram(telegram_id)
    if customer:
        context.user_data["phone"] = customer.get("phone")
        lang = customer.get("language") or lang_for(telegram_lang)
        context.user_data["lang"] = lang
        return lang

    lang = lang_for(telegram_lang)
    context.user_data["lang"] = lang
    return lang
