from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.i18n import locale_ctx, resolve_locale


class LocaleMiddleware(BaseHTTPMiddleware):
    """Resolve EN/AM per request via ?lang= or Accept-Language and expose it to
    schemas (computed label fields) and error handlers through a ContextVar."""

    async def dispatch(self, request: Request, call_next):
        locale = resolve_locale(
            request.query_params.get("lang"),
            request.headers.get("accept-language"),
        )
        token = locale_ctx.set(locale)
        try:
            response = await call_next(request)
        finally:
            locale_ctx.reset(token)
        return response
