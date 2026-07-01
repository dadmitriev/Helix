from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.patient import Gender
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    first_name: str
    last_name: str
    middle_name: str | None = None
    # Required only when role=PATIENT — used to auto-create the patient card
    date_of_birth: date | None = None
    gender: Gender | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    email: EmailStr | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
    first_name: str
    last_name: str
    middle_name: str | None
    is_active: bool
    full_name: str
    created_at: datetime


class UserShort(BaseModel):
    """Compact user reference used inside nested responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    role: UserRole
