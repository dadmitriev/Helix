from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidStatusTransitionError,
    NotFoundError,
    ValidationError,
)
from app.models.lab_order import LabOrder, LabOrderStatus
from app.models.user import User, UserRole
from app.repositories.lab_order_repository import LabOrderRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.lab_order import LabOrderCreate, LabResultsUpdate


class LabOrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = LabOrderRepository(session)
        self.patient_repo = PatientRepository(session)

    # ─── Create (Doctor) ──────────────────────────────────────────────────────

    async def create(self, data: LabOrderCreate, doctor: User) -> LabOrder:
        patient = await self.patient_repo.get_by_id_with_relations(data.patient_id)
        if not patient:
            raise NotFoundError(f"Patient {data.patient_id} not found")

        order = LabOrder(
            patient_id=data.patient_id,
            ordering_doctor_id=doctor.id,
            priority=data.priority,
            requested_panels=data.requested_panels,
            order_notes=data.order_notes,
            status=LabOrderStatus.ORDERED,
            ordered_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create(order)
        # Reload with relations for response
        return await self.repo.get_by_id_full(created.id)

    # ─── Read ─────────────────────────────────────────────────────────────────

    async def get_or_404(self, order_id: UUID) -> LabOrder:
        order = await self.repo.get_by_id_full(order_id)
        if not order:
            raise NotFoundError(f"LabOrder {order_id} not found")
        return order

    async def check_access(self, order: LabOrder, user: User) -> None:
        """Raise ForbiddenError if the user has no right to view this order."""
        if user.role == UserRole.ADMIN:
            return
        if user.role == UserRole.DOCTOR and order.ordering_doctor_id != user.id:
            raise ForbiddenError("You can only access orders you created")
        if user.role == UserRole.LABORATORIAN:
            # Laboratorian can see ORDERED/IN_PROGRESS (any) or their own
            if order.status not in (LabOrderStatus.ORDERED, LabOrderStatus.IN_PROGRESS):
                if order.laboratorian_id != user.id:
                    raise ForbiddenError("Access denied to this order")
        if user.role == UserRole.PATIENT:
            patient = await self.patient_repo.get_by_user_id(user.id)
            if not patient or patient.id != order.patient_id:
                raise ForbiddenError("You can only access your own orders")

    async def list_for_user(
        self,
        user: User,
        status: LabOrderStatus | None,
        patient_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[LabOrder], int]:
        # Resolve patient_id for PATIENT role
        resolved_patient_id = patient_id
        if user.role == UserRole.PATIENT:
            p = await self.patient_repo.get_by_user_id(user.id)
            resolved_patient_id = p.id if p else None

        return await self.repo.list_for_user(
            user_id=user.id,
            user_role=user.role,
            status=status,
            patient_id=resolved_patient_id,
            offset=offset,
            limit=limit,
        )

    # ─── Accept (Laboratorian) ────────────────────────────────────────────────

    async def accept(self, order_id: UUID, laboratorian: User) -> LabOrder:
        order = await self.get_or_404(order_id)
        if order.status != LabOrderStatus.ORDERED:
            raise InvalidStatusTransitionError(
                f"Cannot accept order with status '{order.status.value}'. Expected ORDERED."
            )
        order.status = LabOrderStatus.IN_PROGRESS
        order.laboratorian_id = laboratorian.id
        await self.repo.flush()
        return await self.repo.get_by_id_full(order_id)

    # ─── Update results (Laboratorian) ───────────────────────────────────────

    async def update_results(
        self, order_id: UUID, data: LabResultsUpdate, laboratorian: User
    ) -> LabOrder:
        order = await self.get_or_404(order_id)

        if order.status != LabOrderStatus.IN_PROGRESS:
            raise InvalidStatusTransitionError(
                "Results can only be updated when order is IN_PROGRESS"
            )
        if order.laboratorian_id != laboratorian.id and laboratorian.role != UserRole.ADMIN:
            raise ForbiddenError("You are not assigned to this order")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(order, field, value)
        await self.repo.flush()
        return await self.repo.get_by_id_full(order_id)

    # ─── Submit results (Laboratorian) ───────────────────────────────────────

    async def submit_results(self, order_id: UUID, laboratorian: User) -> LabOrder:
        order = await self.get_or_404(order_id)

        if order.status != LabOrderStatus.IN_PROGRESS:
            raise InvalidStatusTransitionError(
                "Can only submit results when order is IN_PROGRESS"
            )
        if order.laboratorian_id != laboratorian.id and laboratorian.role != UserRole.ADMIN:
            raise ForbiddenError("You are not assigned to this order")

        missing = order.get_missing_fields()
        if missing:
            raise ValidationError(
                f"Cannot submit: missing required fields for requested panels: {missing}"
            )

        order.status = LabOrderStatus.RESULTS_READY
        order.results_submitted_at = datetime.now(timezone.utc)
        await self.repo.flush()
        return await self.repo.get_by_id_full(order_id)

    # ─── Reopen results (Laboratorian / Admin) ────────────────────────────────

    async def reopen_results(self, order_id: UUID, user: User) -> LabOrder:
        order = await self.get_or_404(order_id)

        if order.status != LabOrderStatus.RESULTS_READY:
            raise InvalidStatusTransitionError(
                "Can only reopen from RESULTS_READY status"
            )
        if order.prediction is not None:
            raise ConflictError(
                "Cannot reopen: ML prediction has already been created for this order"
            )

        order.status = LabOrderStatus.IN_PROGRESS
        order.results_submitted_at = None
        await self.repo.flush()
        return await self.repo.get_by_id_full(order_id)

    # ─── Mark concluded (called internally by conclusion service) ─────────────

    async def mark_concluded(self, order_id: UUID) -> None:
        order = await self.get_or_404(order_id)
        order.status = LabOrderStatus.CONCLUDED
        await self.repo.flush()
