import uuid

from pydantic import BaseModel, ConfigDict

from app.models.branches import FacilityType


class BranchCreate(BaseModel):
    name: str
    code: str
    city: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    airport_iata: str | None = None
    facility_type: FacilityType = FacilityType.BRANCH
    latitude: float | None = None
    longitude: float | None = None


class BranchUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None
    airport_iata: str | None = None
    facility_type: FacilityType | None = None
    latitude: float | None = None
    longitude: float | None = None


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
    facility_type: FacilityType
    airport_iata: str | None = None
    latitude: float | None = None
    longitude: float | None = None
