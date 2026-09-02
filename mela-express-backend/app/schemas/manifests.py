import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.i18n import t as _i18n_t
from app.models import ManifestStatus
from app.schemas.common import ManifestCheckpointOut
from app.schemas.parcels import ParcelOut


class ManifestCreate(BaseModel):
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    parcel_ids: list[uuid.UUID]
    driver_name: str | None = None
    vehicle_plate: str | None = None
    notes: str | None = None


class ManifestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    origin_branch_id: uuid.UUID
    destination_branch_id: uuid.UUID
    status: ManifestStatus
    driver_name: str | None = None
    vehicle_plate: str | None = None
    notes: str | None = None
    created_at: datetime
    parcel_count: int = 0

    @computed_field
    @property
    def status_label(self) -> str:
        return _i18n_t(f"manifest_status.{self.status.value}")


class ManifestReceive(BaseModel):
    received_parcel_ids: list[uuid.UUID]


class ManifestCheckpointCreate(BaseModel):
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None


class ManifestDetailOut(ManifestOut):
    parcels: list[ParcelOut] = Field(default_factory=list)
    checkpoints: list[ManifestCheckpointOut] = Field(default_factory=list)
