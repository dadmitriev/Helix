from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from app.models.doctor_conclusion import ConclusionStatus, DoctorConclusion
from app.models.lab_order import LabOrderStatus
from app.models.user import User, UserRole
from app.repositories.conclusion_repository import ConclusionRepository
from app.schemas.conclusion import ConclusionCreate, ConclusionUpdate
from app.services.lab_order_service import LabOrderService


class ConclusionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ConclusionRepository(session)
        self.order_service = LabOrderService(session)

    async def create(
        self, lab_order_id: UUID, data: ConclusionCreate, doctor: User
    ) -> DoctorConclusion:
        order = await self.order_service.get_or_404(lab_order_id)

        if doctor.role != UserRole.ADMIN and order.ordering_doctor_id != doctor.id:
            raise ForbiddenError("Only the ordering doctor can create a conclusion")

        if order.status not in (LabOrderStatus.RESULTS_READY, LabOrderStatus.CONCLUDED):
            raise InvalidStatusTransitionError(
                "Conclusion can only be created when order status is RESULTS_READY or CONCLUDED"
            )

        existing = await self.repo.get_by_lab_order(lab_order_id)
        if existing:
            raise ConflictError(
                "A conclusion already exists for this order. Use PATCH to update it."
            )

        conclusion = DoctorConclusion(
            lab_order_id=lab_order_id,
            doctor_id=doctor.id,
            preliminary_diagnosis=data.preliminary_diagnosis,
            conclusion_text=data.conclusion_text,
            recommendations=data.recommendations,
            agreed_with_ai=data.agreed_with_ai,
            risk_confirmed=data.risk_confirmed,
            follow_up_date=data.follow_up_date,
            status=ConclusionStatus.DRAFT,
        )
        return await self.repo.create(conclusion)

    async def update(
        self, lab_order_id: UUID, data: ConclusionUpdate, doctor: User
    ) -> DoctorConclusion:
        conclusion = await self._get_editable_conclusion(lab_order_id, doctor)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(conclusion, field, value)
        await self.repo.flush()
        return conclusion

    async def send(self, lab_order_id: UUID, doctor: User) -> DoctorConclusion:
        conclusion = await self._get_editable_conclusion(lab_order_id, doctor)
        conclusion.status = ConclusionStatus.SENT
        conclusion.sent_at = datetime.now(timezone.utc)
        await self.repo.flush()
        # Mark the parent order as CONCLUDED
        await self.order_service.mark_concluded(lab_order_id)
        return conclusion

    async def get_for_order(self, lab_order_id: UUID, user: User) -> DoctorConclusion | None:
        order = await self.order_service.get_or_404(lab_order_id)
        await self.order_service.check_access(order, user)
        conclusion = await self.repo.get_by_lab_order(lab_order_id)
        # Patient sees conclusion only after it's sent
        if user.role == UserRole.PATIENT and conclusion and conclusion.status != ConclusionStatus.SENT:
            return None
        return conclusion

    # ─── Private helpers ──────────────────────────────────────────────────────

    async def _get_editable_conclusion(
        self, lab_order_id: UUID, doctor: User
    ) -> DoctorConclusion:
        order = await self.order_service.get_or_404(lab_order_id)

        if doctor.role != UserRole.ADMIN and order.ordering_doctor_id != doctor.id:
            raise ForbiddenError("Only the ordering doctor can modify this conclusion")

        conclusion = await self.repo.get_by_lab_order(lab_order_id)
        if not conclusion:
            raise NotFoundError("No conclusion exists for this order. Use POST to create it.")
        if conclusion.status == ConclusionStatus.SENT:
            raise InvalidStatusTransitionError("Cannot modify a conclusion that has already been sent")
        return conclusion
