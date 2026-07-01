from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doctor_conclusion import DoctorConclusion
from app.repositories.base import BaseRepository


class ConclusionRepository(BaseRepository[DoctorConclusion]):
    model = DoctorConclusion

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_lab_order(self, lab_order_id: UUID) -> DoctorConclusion | None:
        q = (
            select(DoctorConclusion)
            .where(DoctorConclusion.lab_order_id == lab_order_id)
            .options(selectinload(DoctorConclusion.doctor))
        )
        return (await self.session.execute(q)).scalar_one_or_none()
