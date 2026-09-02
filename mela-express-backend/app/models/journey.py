"""Scan events, air legs, and pickup-reminder audit trail."""
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, Numeric, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import gen_uuid
from app.models.parcels import ParcelStatus, _enum


class ParcelJourneyEvent(Base):
    __tablename__ = "parcel_journey_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    to_status: Mapped[ParcelStatus | None] = mapped_column(
        _enum("parcel_status_enum", ParcelStatus), nullable=True
    )
    location_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    facility_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    flight_number: Mapped[str | None] = mapped_column(String(12), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="staff")
    actor_staff_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship(back_populates="journey_events")


class ParcelFlightLeg(Base):
    __tablename__ = "parcel_flight_legs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"), index=True)
    flight_number: Mapped[str] = mapped_column(String(12), index=True)
    airline_iata: Mapped[str | None] = mapped_column(String(4), nullable=True)
    airline_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    origin_iata: Mapped[str | None] = mapped_column(String(4), nullable=True)
    dest_iata: Mapped[str | None] = mapped_column(String(4), nullable=True)
    airway_bill: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    scheduled_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    altitude_m: Mapped[float | None] = mapped_column(Numeric(8, 1), nullable=True)
    heading: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    velocity_ms: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    on_ground: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_position_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parcel: Mapped["Parcel"] = relationship(back_populates="flight_legs")


class PickupReminderLog(Base):
    __tablename__ = "pickup_reminder_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"), index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    recipient_role: Mapped[str] = mapped_column(String(20))
    channel: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
