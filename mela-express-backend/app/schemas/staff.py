import uuid

from pydantic import BaseModel, ConfigDict, computed_field

from app.i18n import t as _i18n_t
from app.models import StaffRole


class StaffCreate(BaseModel):
    name: str
    phone: str
    password: str
    role: StaffRole
    branch_id: uuid.UUID
    email: str | None = None


class StaffUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    password: str | None = None
    role: StaffRole | None = None
    branch_id: uuid.UUID | None = None
    is_active: bool | None = None


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    phone: str
    email: str | None = None
    role: StaffRole
    branch_id: uuid.UUID | None = None
    is_active: bool

    @computed_field
    @property
    def role_label(self) -> str:
        return _i18n_t(f"role.{self.role.value}")
