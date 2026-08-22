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


class ManifestStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(5), unique=True)
    city: Mapped[str] = mapped_column(String(80))
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole, name="staff_role_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]))
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
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode, name="payment_mode_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]))
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="payment_method_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]), default=PaymentStatus.PENDING)

    status: Mapped[ParcelStatus] = mapped_column(Enum(ParcelStatus, name="parcel_status_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]), default=ParcelStatus.CREATED)
    waybill_url: Mapped[str] = mapped_column(String(500), nullable=True)
    pickup_otp: Mapped[str] = mapped_column(String(10), nullable=True)
    otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

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
    from_status: Mapped[ParcelStatus] = mapped_column(Enum(ParcelStatus, name="parcel_status_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=True)
    to_status: Mapped[ParcelStatus] = mapped_column(Enum(ParcelStatus, name="parcel_status_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]))
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
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="payment_method_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]))
    chapa_tx_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]), default=PaymentStatus.PENDING)
    collected_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    override_reason: Mapped[str] = mapped_column(Text, nullable=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="payments")


class TransferManifest(Base):
    __tablename__ = "transfer_manifests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    origin_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))
    destination_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"))
    driver_name: Mapped[str] = mapped_column(String(120), nullable=True)
    vehicle_plate: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[ManifestStatus] = mapped_column(Enum(ManifestStatus, name="manifest_status_enum", native_enum=True, create_type=False, values_callable=lambda x: [e.value for e in x]), default=ManifestStatus.DRAFT)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    origin_branch: Mapped["Branch"] = relationship(foreign_keys=[origin_branch_id])
    destination_branch: Mapped["Branch"] = relationship(foreign_keys=[destination_branch_id])


class ManifestParcel(Base):
    __tablename__ = "manifest_parcels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    manifest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_manifests.id"))
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    received: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"), nullable=True)

    manifest: Mapped["TransferManifest"] = relationship()
    parcel: Mapped["Parcel"] = relationship()


class ManifestCheckpoint(Base):
    __tablename__ = "manifest_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    manifest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_manifests.id"))
    location_name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    manifest: Mapped["TransferManifest"] = relationship()



class ParcelProofOfDelivery(Base):
    __tablename__ = "parcel_proof_of_delivery"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    photo_url: Mapped[str] = mapped_column(String(500))
    signature_url: Mapped[str] = mapped_column(String(500), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship()


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    error_detail: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

