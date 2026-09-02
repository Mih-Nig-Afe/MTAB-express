import enum
import uuid

from sqlalchemy import String, Boolean, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import gen_uuid


class FacilityType(str, enum.Enum):
    BRANCH = "branch"
    AIRPORT = "airport"
    SORTING_HUB = "sorting_hub"


def _facility_enum():
    return Enum(
        FacilityType,
        name="facility_type_enum",
        native_enum=True,
        create_type=False,
        values_callable=lambda x: [e.value for e in x],
    )


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
    facility_type: Mapped[FacilityType] = mapped_column(
        _facility_enum(), default=FacilityType.BRANCH, server_default="branch"
    )
    airport_iata: Mapped[str | None] = mapped_column(String(4), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
