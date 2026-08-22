from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.exceptions import register_exception_handlers
from app.routers import (
    auth, parcels, payments, customers, manifests, branches, staff, reports
)

app = FastAPI(
    title="Mela Express API",
    description="Backend API for Mela Express parcel delivery platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
