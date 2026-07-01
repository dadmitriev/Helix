from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_recommendation import AIRecommendation
from app.models.prediction import Prediction
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    model = Prediction

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_lab_order(self, lab_order_id: UUID) -> Prediction | None:
        q = (
            select(Prediction)
            .where(Prediction.lab_order_id == lab_order_id)
            .options(selectinload(Prediction.ai_recommendation))
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create_with_recommendation(
        self, prediction: Prediction, recommendation: AIRecommendation
    ) -> Prediction:
        self.session.add(prediction)
        await self.session.flush()
        recommendation.prediction_id = prediction.id
        self.session.add(recommendation)
        await self.session.flush()
        await self.session.refresh(prediction)
        return prediction
