import uuid
from datetime import date

from pydantic import BaseModel


class ReportFilter(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    branch_id: uuid.UUID | None = None
    operator_id: uuid.UUID | None = None
