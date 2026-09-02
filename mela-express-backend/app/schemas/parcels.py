import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.i18n import t as _i18n_t
from app.core.carrier_status import carrier_label
from app.models import ParcelStatus, PaymentMode, PaymentMethod, PaymentStatus, SizeCategory, ContentCategory
from app.schemas.common import StatusHistoryOut, ManifestCheckpointOut


class ParcelCreate(BaseModel):
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    sender_phone: str
    sender_name: str | None = None
    receiver_name: str
    receiver_phone: str
    description: str | None = None
    weight_kg: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    size_category: SizeCategory | None = None
    content_category: ContentCategory = ContentCategory.GENERAL
    declared_value: float | None = None
    price: float | None = None
    payment_mode: PaymentMode
    payment_method: PaymentMethod | None = None


class ClassificationPreview(BaseModel):
    weight_kg: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    content_category: ContentCategory = ContentCategory.GENERAL


class ClassificationPreviewOut(BaseModel):
    size_category: SizeCategory
    volumetric_weight_kg: float
    chargeable_weight_kg: float
    suggested_price: float


class ParcelScanRequest(BaseModel):
    code: str
    note: str | None = None
    flight_number: str | None = None
    airline_iata: str | None = None


class ParcelScanOut(BaseModel):
    ok: bool = True
    tracking_code: str
    from_status: ParcelStatus
    to_status: ParcelStatus
    status_label: str
    station: str
    message: str
    track_url: str


class ParcelStatusUpdate(BaseModel):
    to_status: ParcelStatus
    note: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    flight_number: str | None = None
    airline_iata: str | None = None
    origin_airport_iata: str | None = None
    destination_airport_iata: str | None = None
    scheduled_departure: datetime | None = None
    scheduled_arrival: datetime | None = None
    airway_bill: str | None = None


class FlightLegAttach(BaseModel):
    flight_number: str
    airline_iata: str | None = None
    origin_airport_iata: str | None = None
    destination_airport_iata: str | None = None
    scheduled_departure: datetime | None = None
    scheduled_arrival: datetime | None = None
    airway_bill: str | None = None


class JourneyEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    to_status: ParcelStatus | None = None
    location_name: str | None = None
    facility_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    flight_number: str | None = None
    note: str | None = None
    source: str
    created_at: datetime


class FlightLegOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    flight_number: str
    airline_iata: str | None = None
    airline_name: str | None = None
    origin_iata: str | None = None
    dest_iata: str | None = None
    airway_bill: str | None = None
    status: str
    scheduled_departure: datetime | None = None
    scheduled_arrival: datetime | None = None
    actual_departure: datetime | None = None
    actual_arrival: datetime | None = None
    delay_minutes: int = 0
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    heading: float | None = None
    velocity_ms: float | None = None
    on_ground: bool | None = None
    last_position_at: datetime | None = None
    provider: str | None = None


class EtaOut(BaseModel):
    promised_delivery_at: datetime | None = None
    current_eta_at: datetime | None = None
    remaining_minutes: int = 0
    delay_minutes: int = 0
    on_time: bool | None = None


class ProofOfDeliveryUpload(BaseModel):
    photo_url: str
    signature_url: str | None = None
    notes: str | None = None


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
    origin_branch_code: str | None = None
    destination_branch_code: str | None = None
    sender_phone: str | None = None
    sender_id: uuid.UUID
    description: str | None = None
    weight_kg: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    size_category: SizeCategory | None = None
    content_category: ContentCategory | None = None
    volumetric_weight_kg: float | None = None
    chargeable_weight_kg: float | None = None
    declared_value: float | None = None
    waybill_url: str | None = None
    track_url: str | None = None
    origin_airport_iata: str | None = None
    dest_airport_iata: str | None = None
    promised_delivery_at: datetime | None = None
    current_eta_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def status_label(self) -> str:
        return _i18n_t(f"parcel_status.{self.status.value}")

    @computed_field
    @property
    def payment_status_label(self) -> str:
        return _i18n_t(f"payment_status.{self.payment_status.value}")

    @computed_field
    @property
    def payment_mode_label(self) -> str:
        return _i18n_t(f"payment_mode.{self.payment_mode.value}")

    @computed_field
    @property
    def payment_method_label(self) -> str | None:
        return _i18n_t(f"payment_method.{self.payment_method.value}") if self.payment_method else None


class ParcelDetailOut(ParcelOut):
    status_history: list[StatusHistoryOut] = Field(default_factory=list)
    pickup_otp: str | None = None
    journey_events: list[JourneyEventOut] = Field(default_factory=list)
    flight: FlightLegOut | None = None
    eta: EtaOut | None = None
    allowed_next: list[ParcelStatus] = Field(default_factory=list)


class ParcelTrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tracking_code: str
    status: ParcelStatus
    payment_status: PaymentStatus
    origin_branch_name: str
    destination_branch_name: str
    status_history: list[StatusHistoryOut] = Field(default_factory=list)
    checkpoints: list[ManifestCheckpointOut] = Field(default_factory=list)
    journey_events: list[JourneyEventOut] = Field(default_factory=list)
    flight: FlightLegOut | None = None
    eta: EtaOut | None = None
    created_at: datetime

    @computed_field
    @property
    def status_label(self) -> str:
        return _i18n_t(f"parcel_status.{self.status.value}")

    @computed_field
    @property
    def payment_status_label(self) -> str:
        return _i18n_t(f"payment_status.{self.payment_status.value}")

    @computed_field
    @property
    def carrier_status_label(self) -> str:
        return carrier_label(self.status)
