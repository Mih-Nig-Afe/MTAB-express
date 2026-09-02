from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.state_machine import InvalidTransition
from app.i18n import terr

class MelaException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

class NotFoundError(MelaException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(404, detail)

class ForbiddenError(MelaException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)

class PaymentRequired(MelaException):
    def __init__(self, detail: str = "Payment required"):
        super().__init__(402, detail)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MelaException)
    async def mela_exception_handler(request: Request, exc: MelaException):
        return JSONResponse(status_code=exc.status_code, content={"detail": terr(exc.detail)})

    @app.exception_handler(InvalidTransition)
    async def invalid_transition_handler(request: Request, exc: InvalidTransition):
        return JSONResponse(status_code=400, content={"detail": terr(str(exc))})

    from fastapi import HTTPException

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Localize known static details raised via HTTPException across routers
        # (OTP messages, permission denials, etc.). Unknown strings pass through.
        detail = exc.detail if isinstance(exc.detail, str) else terr(str(exc.detail))
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": terr(detail)},
            headers=getattr(exc, "headers", None),
        )
