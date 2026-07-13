"""
Core data model. Mirrors the schema laid out in the architecture doc:
branches, staff users, customers, parcels, status history, payments, manifests.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, ForeignKey, Numeric, DateTime, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


class ParcelStatus(str, enum.Enum):
    CREATED = "created"
    RECEIVED_AT_ORIGIN = "received_at_origin"
    IN_TRANSIT = "in_transit"
    ARRIVED_AT_DESTINATION = "arrived_at_destination"
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


class StaffRole(str, enum.Enum):
    OPERATOR = "operator"
    MANAGER = "manager"
    DRIVER = "driver"
    ADMIN = "admin"


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole))
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    branch: Mapped["Branch"] = relationship()


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    telegram_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=True)


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    tracking_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    origin_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))
    destination_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))

    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"))
    receiver_name: Mapped[str] = mapped_column(String(120))
    receiver_phone: Mapped[str] = mapped_column(String(30))
    receiver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Numeric(6, 2), nullable=True)
    declared_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)

    price: Mapped[float] = mapped_column(Numeric(10, 2))
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode))
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    status: Mapped[ParcelStatus] = mapped_column(Enum(ParcelStatus), default=ParcelStatus.CREATED)

    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    origin_branch: Mapped["Branch"] = relationship(foreign_keys=[origin_branch_id])
    destination_branch: Mapped["Branch"] = relationship(foreign_keys=[destination_branch_id])
    status_history: Mapped[list["ParcelStatusHistory"]] = relationship(back_populates="parcel")
    payments: Mapped[list["Payment"]] = relationship(back_populates="parcel")


class ParcelStatusHistory(Base):
    __tablename__ = "parcel_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    from_status: Mapped[ParcelStatus] = mapped_column(Enum(ParcelStatus), nullable=True)
    to_status: Mapped[ParcelStatus] = mapped_column(Enum(ParcelStatus))
    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship(back_populates="status_history")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    chapa_tx_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    collected_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship(back_populates="payments")
