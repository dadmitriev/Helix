from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.patient import Gender


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    date_of_birth: date
    gender: Gender
    phone: str | None = None
    address: str | None = None
    family_history_diabetes: bool = False
    # Link to existing system user account (optional)
    user_id: UUID | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = None
    address: str | None = None
    family_history_diabetes: bool | None = None
    user_id: UUID | None = None


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    medical_record_number: str
    first_name: str
    last_name: str
    middle_name: str | None
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
    phone: str | None
    address: str | None
    family_history_diabetes: bool
    user_id: UUID | None
    created_by: UUID
    created_at: datetime


class PatientShort(BaseModel):
    """Compact patient reference used inside nested responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    medical_record_number: str
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
