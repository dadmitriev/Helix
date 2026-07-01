from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.doctor_conclusion import ConclusionStatus
from app.models.prediction import RiskLevel
from app.schemas.user import UserShort


class ConclusionCreate(BaseModel):
    preliminary_diagnosis: str | None = None
    conclusion_text: str
    recommendations: str | None = None
    agreed_with_ai: bool = True
    risk_confirmed: RiskLevel | None = None
    follow_up_date: date | None = None


class ConclusionUpdate(BaseModel):
    preliminary_diagnosis: str | None = None
    conclusion_text: str | None = None
    recommendations: str | None = None
    agreed_with_ai: bool | None = None
    risk_confirmed: RiskLevel | None = None
    follow_up_date: date | None = None


class ConclusionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lab_order_id: UUID
    preliminary_diagnosis: str | None
    conclusion_text: str
    recommendations: str | None
    agreed_with_ai: bool
    risk_confirmed: RiskLevel | None
    follow_up_date: date | None
    status: ConclusionStatus
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
    doctor: UserShort
