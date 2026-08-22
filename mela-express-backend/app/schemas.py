import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field

from app.models import ParcelStatus, PaymentMode, PaymentMethod, PaymentStatus, StaffRole, ManifestStatus

class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class StaffCreate(BaseModel):
    name: str
    phone: str
    password: str
    role: StaffRole
    branch_id: uuid.UUID
    email: str | None = None

class StaffUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: StaffRole | None = None
    branch_id: uuid.UUID | None = None
    is_active: bool | None = None

class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    phone: str
    email: str | None = None
    role: StaffRole
    branch_id: uuid.UUID | None = None
    is_active: bool

class BranchCreate(BaseModel):
    name: str
    code: str
    city: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None

class BranchUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None

class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    code: str
    city: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool

class CustomerLink(BaseModel):
    phone: str
    telegram_id: str
    name: str | None = None

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    phone: str
    telegram_id: str | None = None
    name: str | None = None

class ManifestCreate(BaseModel):
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    parcel_ids: list[uuid.UUID]
    driver_name: str | None = None
    vehicle_plate: str | None = None
    notes: str | None = None

class ManifestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    status: ManifestStatus
    driver_name: str | None = None
    vehicle_plate: str | None = None
    notes: str | None = None
    created_at: datetime
    parcel_count: int = 0

class ManifestReceive(BaseModel):
    received_parcel_ids: list[uuid.UUID]

class ProofOfDeliveryUpload(BaseModel):
    photo_url: str
    signature_url: str | None = None
    notes: str | None = None

class CashCollectRequest(BaseModel):
    override_reason: str | None = None

class ReportFilter(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    branch_id: uuid.UUID | None = None
    operator_id: uuid.UUID | None = None

class ParcelCreate(BaseModel):
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    sender_phone: str
    sender_name: str | None = None
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

class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    from_status: ParcelStatus | None = None
    to_status: ParcelStatus
    changed_by: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    note: str | None = None
    timestamp: datetime

class ParcelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tracking_code: str
    status: ParcelStatus
    payment_status: PaymentStatus
    payment_mode: PaymentMode
    payment_method: PaymentMethod | None = None
    price: float
    receiver_name: str
    receiver_phone: str
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    sender_id: uuid.UUID
    description: str | None = None
    weight_kg: float | None = None
    declared_value: float | None = None
    waybill_url: str | None = None
    created_at: datetime
    updated_at: datetime

class ParcelDetailOut(ParcelOut):
    status_history: list[StatusHistoryOut] = Field(default_factory=list)
    pickup_otp: str | None = None

class ManifestCheckpointCreate(BaseModel):
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None

class ManifestCheckpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    manifest_id: uuid.UUID
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None
    created_at: datetime

class ManifestDetailOut(ManifestOut):
    parcels: list[ParcelOut] = Field(default_factory=list)
    checkpoints: list[ManifestCheckpointOut] = Field(default_factory=list)

class ParcelTrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tracking_code: str
    status: ParcelStatus
    payment_status: PaymentStatus
    origin_branch_name: str
    destination_branch_name: str
    status_history: list[StatusHistoryOut] = Field(default_factory=list)
    checkpoints: list[ManifestCheckpointOut] = Field(default_factory=list)
    created_at: datetime

class ChapaInitRequest(BaseModel):
    parcel_id: uuid.UUID
    customer_email: str | None = None

class ChapaWebhookPayload(BaseModel):
    tx_ref: str
    status: str
    amount: str | None = None

class OTPGenerateOut(BaseModel):
    parcel_id: uuid.UUID
    tracking_code: str
    pickup_otp: str
    receiver_phone: str
    message: str

class VerifyPickupRequest(BaseModel):
    otp: str
    signature_url: str | None = None
    photo_url: str | None = None
    notes: str | None = None


