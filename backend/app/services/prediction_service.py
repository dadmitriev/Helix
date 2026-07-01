from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, InvalidStatusTransitionError, NotFoundError
from app.ml.predictor import predictor
from app.models.ai_recommendation import AIRecommendation
from app.models.lab_order import LabOrderStatus
from app.models.prediction import Prediction
from app.models.user import User, UserRole
from app.repositories.lab_order_repository import LabOrderRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.lab_order_service import LabOrderService


class PredictionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pred_repo = PredictionRepository(session)
        self.order_repo = LabOrderRepository(session)
        self.order_service = LabOrderService(session)

    async def run_prediction(self, lab_order_id: UUID, doctor: User) -> Prediction:
        order = await self.order_service.get_or_404(lab_order_id)

        # Access: only the ordering doctor or admin
        if doctor.role != UserRole.ADMIN and order.ordering_doctor_id != doctor.id:
            raise ForbiddenError("Only the ordering doctor can run predictions")

        if order.status not in (LabOrderStatus.RESULTS_READY, LabOrderStatus.CONCLUDED):
            raise InvalidStatusTransitionError(
                "Prediction can only be run when order status is RESULTS_READY or CONCLUDED"
            )

        # Remove old prediction if exists (re-run allowed)
        existing = await self.pred_repo.get_by_lab_order(lab_order_id)
        if existing:
            await self.pred_repo.delete(existing)

        # Run ML
        result = predictor.predict(order)
        pd = result["prediction_data"]
        rd = result["recommendation_data"]

        prediction = Prediction(
            lab_order_id=lab_order_id,
            model_name=pd["model_name"],
            model_version=pd["model_version"],
            risk_score=pd["risk_score"],
            risk_level=pd["risk_level"],
            homa_ir=pd["homa_ir"],
            feature_importances=pd["feature_importances"],
            raw_output=pd["raw_output"],
            predicted_at=pd["predicted_at"],
        )

        recommendation = AIRecommendation(
            summary=rd["summary"],
            recommendations=rd["recommendations"],
            warning_flags=rd["warning_flags"],
            generated_at=rd["generated_at"],
        )

        saved = await self.pred_repo.create_with_recommendation(prediction, recommendation)
        # Reload with relations
        return await self.pred_repo.get_by_lab_order(lab_order_id)

    async def get_for_order(self, lab_order_id: UUID, user: User) -> Prediction | None:
        order = await self.order_service.get_or_404(lab_order_id)
        await self.order_service.check_access(order, user)
        return await self.pred_repo.get_by_lab_order(lab_order_id)
