from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dob: date | None = None
    sex: str | None = Field(default=None, max_length=20)
    department: str | None = Field(default=None, max_length=100)
    raw_note: str = Field(min_length=1, max_length=5000)


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    dob: date | None
    sex: str | None
    department: DepartmentOut | None
    raw_note: str
    created_at: datetime
    updated_at: datetime