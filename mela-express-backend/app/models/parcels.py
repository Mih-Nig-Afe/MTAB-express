import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, ForeignKey, Numeric, DateTime, Text, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import gen_uuid


class ParcelStatus(str, enum.Enum):
    CREATED = "created"
    RECEIVED_AT_ORIGIN = "received_at_origin"
    PROCESSED_AT_ORIGIN = "processed_at_origin"
    DISPATCHED_FROM_ORIGIN = "dispatched_from_origin"
    IN_TRANSIT = "in_transit"
    ARRIVED_ORIGIN_AIRPORT = "arrived_origin_airport"
    CHECKED_IN_FLIGHT = "checked_in_flight"
    DEPARTED = "departed"
    ARRIVED_DESTINATION_AIRPORT = "arrived_destination_airport"
    RELEASED_FROM_AIRPORT = "released_from_airport"
    ARRIVED_AT_DESTINATION = "arrived_at_destination"
    DISTRIBUTED_TO_BRANCH = "distributed_to_branch"
    READY_FOR_PICKUP = "ready_for_pickup"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    LOST = "lost"
    ON_HOLD = "on_hold"


class PaymentMode(str, enum.Enum):
    BEFORE = "before"   # prepaid at intake
    AFTER = "after"      # collected on delivery / by receiver


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHAPA = "chapa"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class SizeCategory(str, enum.Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    OVERSIZED = "oversized"


class ContentCategory(str, enum.Enum):
    DOCUMENTS = "documents"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    FRAGILE = "fragile"
    GENERAL = "general"


def _enum(name: str, cls):
    return Enum(cls, name=name, native_enum=True, create_type=False,
                values_callable=lambda x: [e.value for e in x])


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    tracking_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    origin_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))
    destination_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))

    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"))
    receiver_name: Mapped[str] = mapped_column(String(120))
    receiver_phone: Mapped[str] = mapped_column(String(30))
    receiver_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id"), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    length_cm: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    width_cm: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    size_category: Mapped[SizeCategory | None] = mapped_column(
        _enum("size_category_enum", SizeCategory), nullable=True
    )
    content_category: Mapped[ContentCategory | None] = mapped_column(
        _enum("content_category_enum", ContentCategory), nullable=True, default=ContentCategory.GENERAL
    )
    volumetric_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    chargeable_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    declared_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    price: Mapped[float] = mapped_column(Numeric(10, 2))
    payment_mode: Mapped[PaymentMode] = mapped_column(_enum("payment_mode_enum", PaymentMode))
    payment_method: Mapped[PaymentMethod | None] = mapped_column(_enum("payment_method_enum", PaymentMethod), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(_enum("payment_status_enum", PaymentStatus), default=PaymentStatus.PENDING)

    status: Mapped[ParcelStatus] = mapped_column(_enum("parcel_status_enum", ParcelStatus), default=ParcelStatus.CREATED)
    waybill_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pickup_otp: Mapped[str | None] = mapped_column(String(10), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    origin_airport_iata: Mapped[str | None] = mapped_column(String(4), nullable=True)
    dest_airport_iata: Mapped[str | None] = mapped_column(String(4), nullable=True)
    promised_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_eta_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_reminders_sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_pickup_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    origin_branch: Mapped["Branch"] = relationship(foreign_keys=[origin_branch_id])
    destination_branch: Mapped["Branch"] = relationship(foreign_keys=[destination_branch_id])
    sender: Mapped["Customer"] = relationship(foreign_keys=[sender_id])
    status_history: Mapped[list["ParcelStatusHistory"]] = relationship(back_populates="parcel")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="parcel")
    journey_events: Mapped[list["ParcelJourneyEvent"]] = relationship(
        "ParcelJourneyEvent", back_populates="parcel"
    )
    flight_legs: Mapped[list["ParcelFlightLeg"]] = relationship(
        "ParcelFlightLeg", back_populates="parcel"
    )


class ParcelStatusHistory(Base):
    __tablename__ = "parcel_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    from_status: Mapped[ParcelStatus | None] = mapped_column(_enum("parcel_status_enum", ParcelStatus), nullable=True)
    to_status: Mapped[ParcelStatus] = mapped_column(_enum("parcel_status_enum", ParcelStatus))
    changed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("branches.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship(back_populates="status_history")


class ParcelProofOfDelivery(Base):
    __tablename__ = "parcel_proof_of_delivery"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    photo_url: Mapped[str] = mapped_column(String(500))
    signature_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship()
