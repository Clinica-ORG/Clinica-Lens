from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Department Schemas
class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


# Universal Vitals Sub-Model
class UniversalVitals(BaseModel):
    blood_pressure: str | None = Field(default=None, example="118/76")
    heart_rate: int | None = Field(default=None, example=80)
    temperature_c: float | None = Field(default=None, example=37)


# Patient Status Schemas
class PatientStatusCreate(BaseModel):
    recorded_at: datetime = Field(default_factory=datetime.now)
    acuity_level: str = Field(default="Stable", example="Stable")
    raw_note: str = Field(
        min_length=1,
        max_length=10000,
        example="Patient presented with mild chest tightness.",
    )
    vitals: UniversalVitals | None = None
    department_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Dynamic ward-specific observations (e.g., OGTT (Oral Glucose Tolerance Test), gestational age, etc.)",
        examples=[
            {
                "gestational_age_weeks": 28,
                "fetal_heart_rate_bpm": 145,
                "fundal_height_cm": 27,
            }
        ],
    )


# Patient Schemas
class PatientCreate(BaseModel):
    # Medical Record Number
    mrn: str = Field(min_length=3, max_length=50, example="MRN-98123")
    name: str = Field(min_length=1, max_length=200, example="Helen Tran")
    # Date of birth
    dob: date | None = None
    sex: str | None = Field(default=None, max_length=20, example="female")
    department: str = Field(min_length=1, max_length=100, example="Obstetrics")
    initial_status: PatientStatusCreate


# Patient Status Output Schema when GET
class PatientStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    recorded_at: datetime
    acuity_level: str
    raw_note: str
    blood_pressure: str | None
    heart_rate: int | None
    temperature_c: float | None
    department_data: dict[str, Any]
    created_at: datetime


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mrn: str
    name: str
    dob: date | None = None
    sex: str | None = None
    status: str
    department_id: UUID | None = None
    statuses: list[PatientStatusOut] = []
