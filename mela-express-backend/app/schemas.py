import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models import ParcelStatus, PaymentMode, PaymentMethod, PaymentStatus


class ParcelCreate(BaseModel):
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    sender_phone: str
    receiver_name: str
    receiver_phone: str
    description: str | None = None
    weight_kg: float | None = None
    declared_value: float | None = None
    price: float
    payment_mode: PaymentMode
    payment_method: PaymentMethod | None = None


class ParcelStatusUpdate(BaseModel):
    to_status: ParcelStatus
    note: str | None = None


class ParcelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tracking_code: str
    status: ParcelStatus
    payment_status: PaymentStatus
    payment_mode: PaymentMode
    price: float
    receiver_name: str
    receiver_phone: str
    created_at: datetime


class ChapaInitRequest(BaseModel):
    parcel_id: uuid.UUID
    customer_email: str | None = None  # Chapa requires an email field; use a placeholder if none on file


class ChapaWebhookPayload(BaseModel):
    """
    Shape of what Chapa sends. Verify against Chapa's current webhook docs before
    launch — field names have changed between API versions in the past.
    """
    tx_ref: str
    status: str
    amount: str | None = None
