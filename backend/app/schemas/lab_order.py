from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.lab_order import ALL_PANELS, LabOrderPriority, LabOrderStatus
from app.schemas.patient import PatientShort
from app.schemas.user import UserShort


class LabOrderCreate(BaseModel):
    patient_id: UUID
    priority: LabOrderPriority = LabOrderPriority.ROUTINE
    requested_panels: list[str]
    order_notes: str | None = None

    @field_validator("requested_panels")
    @classmethod
    def validate_panels(cls, v: list[str]) -> list[str]:
        invalid = [p for p in v if p not in ALL_PANELS]
        if invalid:
            raise ValueError(f"Unknown panels: {invalid}. Valid: {ALL_PANELS}")
        if not v:
            raise ValueError("At least one panel must be requested")
        return v


class LabResultsUpdate(BaseModel):
    """Payload from laboratorian when filling in test results (partial update allowed)."""
    analysis_date: date | None = None
    analysis_time: time | None = None
    lab_notes: str | None = None

    glucose: Decimal | None = None
    hba1c: Decimal | None = None
    insulin: Decimal | None = None
    bmi: Decimal | None = None
    waist_circumference: Decimal | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    total_cholesterol: Decimal | None = None
    hdl_cholesterol: Decimal | None = None
    ldl_cholesterol: Decimal | None = None
    triglycerides: Decimal | None = None


class LabResultsView(BaseModel):
    """Nested results block returned in LabOrderRead."""
    model_config = ConfigDict(from_attributes=True)

    analysis_date: date | None
    analysis_time: time | None
    lab_notes: str | None
    results_submitted_at: datetime | None

    glucose: Decimal | None
    hba1c: Decimal | None
    insulin: Decimal | None
    bmi: Decimal | None
    waist_circumference: Decimal | None
    systolic_bp: int | None
    diastolic_bp: int | None
    total_cholesterol: Decimal | None
    hdl_cholesterol: Decimal | None
    ldl_cholesterol: Decimal | None
    triglycerides: Decimal | None


class LabOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: LabOrderStatus
    priority: LabOrderPriority
    requested_panels: list[str]
    order_notes: str | None
    ordered_at: datetime
    created_at: datetime

    patient: PatientShort
    ordering_doctor: UserShort
    laboratorian: UserShort | None

    results: LabResultsView | None = None

    @classmethod
    def from_orm_with_results(cls, order) -> "LabOrderRead":
        data = cls.model_validate(order)
        data.results = LabResultsView.model_validate(order)
        return data


class LabOrderShort(BaseModel):
    """Compact representation for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: LabOrderStatus
    priority: LabOrderPriority
    ordered_at: datetime
    requested_panels: list[str]
    patient: PatientShort
    ordering_doctor: UserShort
    laboratorian: UserShort | None
