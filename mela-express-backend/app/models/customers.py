import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import gen_uuid


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    telegram_id: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Preferred UI/message language ("en" | "am") — set via Telegram /lang or API.
    language: Mapped[str] = mapped_column(String(5), default="en", server_default="en", nullable=True)
