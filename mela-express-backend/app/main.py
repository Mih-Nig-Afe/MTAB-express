from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.exceptions import register_exception_handlers
from app.i18n.middleware import LocaleMiddleware
from app.core.brand import brand_name
from app.routers import (
    auth, parcels, payments, customers, manifests, branches, staff, reports, customer_portal, public_config
)

_api_title = brand_name() or "Parcel"
app = FastAPI(
    title=f"{_api_title} API",
    description=f"Backend API for {_api_title} parcel delivery platform",
    version="1.0.0"
)


app.add_middleware(LocaleMiddleware)

# Explicit origin allow-list (wildcard "*" is unsafe with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(parcels.router)
app.include_router(payments.router)
app.include_router(customers.router)
app.include_router(manifests.router)
app.include_router(branches.router)
app.include_router(staff.router)
app.include_router(reports.router)
app.include_router(customer_portal.router)
app.include_router(public_config.router)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
