import uuid

from pydantic import BaseModel


class CashCollectRequest(BaseModel):
    override_reason: str | None = None


class ChapaInitRequest(BaseModel):
    # Either the parcel UUID (dashboard) or its tracking_code (Telegram bot).
    parcel_id: uuid.UUID | None = None
    tracking_code: str | None = None
    customer_email: str | None = None


class ChapaWebhookPayload(BaseModel):
    tx_ref: str
    status: str
    amount: str | None = None
