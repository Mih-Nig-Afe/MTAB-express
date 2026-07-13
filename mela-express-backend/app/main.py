from fastapi import FastAPI

from app.routers import parcels, payments

app = FastAPI(title="Mela Express API")

app.include_router(parcels.router)
app.include_router(payments.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
