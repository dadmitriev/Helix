from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doctor_conclusion import DoctorConclusion
from app.models.lab_order import LabOrder, LabOrderStatus
from app.models.prediction import Prediction
from app.models.user import UserRole
from app.repositories.base import BaseRepository


def _order_with_relations():
    return (
        selectinload(LabOrder.patient),
        selectinload(LabOrder.ordering_doctor),
        selectinload(LabOrder.laboratorian),
        selectinload(LabOrder.prediction).selectinload(Prediction.ai_recommendation),
        selectinload(LabOrder.conclusion).selectinload(DoctorConclusion.doctor),
    )


class LabOrderRepository(BaseRepository[LabOrder]):
    model = LabOrder

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id_full(self, order_id: UUID) -> LabOrder | None:
        q = (
            select(LabOrder)
            .where(LabOrder.id == order_id)
            .options(*_order_with_relations())
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        user_role: UserRole,
        status: LabOrderStatus | None = None,
        patient_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[LabOrder], int]:
        """
        Returns orders filtered by role:
        - DOCTOR: sees orders they created (ordering_doctor_id)
        - LABORATORIAN: sees ORDERED + IN_PROGRESS (any) + their own in other statuses
        - PATIENT: sees orders linked to their patient card
        - ADMIN: sees all
        """
        base = select(LabOrder).options(*_order_with_relations())

        if user_role == UserRole.DOCTOR:
            base = base.where(LabOrder.ordering_doctor_id == user_id)
        elif user_role == UserRole.LABORATORIAN:
            from sqlalchemy import or_
            base = base.where(
                or_(
                    LabOrder.status.in_([LabOrderStatus.ORDERED, LabOrderStatus.IN_PROGRESS]),
                    LabOrder.laboratorian_id == user_id,
                )
            )
        elif user_role == UserRole.PATIENT:
            # Patient can only see their own — patient_id must be resolved by caller
            if patient_id:
                base = base.where(LabOrder.patient_id == patient_id)
            else:
                # No patient card linked → empty result
                return [], 0

        if status is not None:
            base = base.where(LabOrder.status == status)
        if patient_id is not None and user_role != UserRole.PATIENT:
            base = base.where(LabOrder.patient_id == patient_id)

        base = base.order_by(LabOrder.ordered_at.desc())

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        q = base.offset(offset).limit(limit)
        orders = list((await self.session.execute(q)).scalars().all())
        return orders, total

    async def get_for_patient(self, patient_id: UUID) -> list[LabOrder]:
        q = (
            select(LabOrder)
            .where(LabOrder.patient_id == patient_id)
            .options(*_order_with_relations())
            .order_by(LabOrder.ordered_at.desc())
        )
        return list((await self.session.execute(q)).scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        q = select(LabOrder.status, func.count()).group_by(LabOrder.status)
        rows = (await self.session.execute(q)).all()
        return {row[0].value: row[1] for row in rows}
