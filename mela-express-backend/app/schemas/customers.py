import uuid

from pydantic import BaseModel, ConfigDict


class CustomerLink(BaseModel):
    phone: str
    telegram_id: str
    name: str | None = None


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    phone: str
    telegram_id: str | None = None
    name: str | None = None
    language: str | None = "en"


class CustomerLanguageUpdate(BaseModel):
    telegram_id: str | None = None
    phone: str | None = None
    language: str  # "en" | "am"
