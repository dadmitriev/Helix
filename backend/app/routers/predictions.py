from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBSession, require_doctor
from app.models.user import User
from app.schemas.prediction import (
    DISCLAIMER,
    AIRecommendationRead,
    PredictionFullResponse,
    PredictionRead,
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/lab-orders", tags=["Predictions"])


@router.post("/{order_id}/predict", response_model=PredictionFullResponse, status_code=201)
async def run_prediction(
    order_id: UUID,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    """
    Doctor runs ML risk assessment.
    If a prediction already exists, it is replaced with a fresh one.
    """
    service = PredictionService(session)
    prediction = await service.run_prediction(order_id, current_user)

    return PredictionFullResponse(
        prediction=PredictionRead.model_validate(prediction),
        ai_recommendation=AIRecommendationRead.model_validate(prediction.ai_recommendation),
        disclaimer=DISCLAIMER,
    )


@router.get("/{order_id}/prediction", response_model=PredictionFullResponse | None)
async def get_prediction(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
):
    service = PredictionService(session)
    prediction = await service.get_for_order(order_id, current_user)
    if prediction is None:
        return None

    return PredictionFullResponse(
        prediction=PredictionRead.model_validate(prediction),
        ai_recommendation=AIRecommendationRead.model_validate(prediction.ai_recommendation),
        disclaimer=DISCLAIMER,
    )
