from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.prediction import RiskLevel


DISCLAIMER = (
    "Данный результат является вспомогательным инструментом поддержки "
    "принятия решений и не является медицинским диагнозом. "
    "Окончательное клиническое заключение принимается исключительно врачом."
)


class RecommendationItem(BaseModel):
    category: str
    text: str
    priority: str  # "HIGH" | "MEDIUM" | "LOW"


class AIRecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    summary: str
    recommendations: list[RecommendationItem]
    warning_flags: list[str]
    generated_at: datetime


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lab_order_id: UUID
    model_name: str
    model_version: str
    risk_score: Decimal
    risk_level: RiskLevel
    homa_ir: Decimal | None
    feature_importances: dict
    predicted_at: datetime


class PredictionFullResponse(BaseModel):
    """Complete prediction response returned to the doctor after running ML."""
    prediction: PredictionRead
    ai_recommendation: AIRecommendationRead
    disclaimer: str = DISCLAIMER


class PredictionWithRecommendation(BaseModel):
    """Nested response inside LabOrderDetailResponse."""
    model_config = ConfigDict(from_attributes=True)

    prediction: PredictionRead | None
    ai_recommendation: AIRecommendationRead | None
    disclaimer: str = DISCLAIMER
