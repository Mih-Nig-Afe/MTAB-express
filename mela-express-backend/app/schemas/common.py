import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ManifestCheckpoint, ParcelStatus


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    from_status: ParcelStatus | None = None
    to_status: ParcelStatus
    changed_by: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    note: str | None = None
    timestamp: datetime


class ManifestCheckpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    manifest_id: uuid.UUID
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None
    created_at: datetime
