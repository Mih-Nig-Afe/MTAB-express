import uuid
from datetime import datetime

from sqlalchemy import String, Enum, ForeignKey, Numeric, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import gen_uuid
from app.models.parcels import PaymentMethod, PaymentStatus


def _enum(name: str, cls):
    return Enum(cls, name=name, native_enum=True, create_type=False,
                values_callable=lambda x: [e.value for e in x])


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    method: Mapped[PaymentMethod] = mapped_column(_enum("payment_method_enum", PaymentMethod))
    chapa_tx_ref: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(_enum("payment_status_enum", PaymentStatus), default=PaymentStatus.PENDING)
    collected_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="payments")
