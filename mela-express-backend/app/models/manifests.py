import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, ForeignKey, Numeric, DateTime, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import gen_uuid


class ManifestStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    CANCELLED = "cancelled"


def _enum(name: str, cls):
    return Enum(cls, name=name, native_enum=True, create_type=False,
                values_callable=lambda x: [e.value for e in x])


class TransferManifest(Base):
    __tablename__ = "transfer_manifests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    origin_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))
    destination_branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_users.id"))
    driver_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vehicle_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[ManifestStatus] = mapped_column(_enum("manifest_status_enum", ManifestStatus), default=ManifestStatus.DRAFT)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_users.id"), nullable=True)

    manifest: Mapped["TransferManifest"] = relationship()
    parcel: Mapped["Parcel"] = relationship()


class ManifestCheckpoint(Base):
    __tablename__ = "manifest_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    manifest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_manifests.id"))
    location_name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    manifest: Mapped["TransferManifest"] = relationship()
