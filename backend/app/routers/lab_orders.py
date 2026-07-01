from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    DBSession,
    require_doctor,
    require_laboratorian,
)
from app.core.exceptions import ForbiddenError
from app.models.lab_order import LabOrderStatus
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.lab_order import (
    LabOrderCreate,
    LabOrderRead,
    LabOrderShort,
    LabResultsUpdate,
)
from app.services.lab_order_service import LabOrderService

router = APIRouter(prefix="/lab-orders", tags=["Lab Orders"])


@router.get("", response_model=PaginatedResponse[LabOrderShort])
async def list_lab_orders(
    session: DBSession,
    current_user: CurrentUser,
    status: LabOrderStatus | None = Query(None),
    patient_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    service = LabOrderService(session)
    items, total = await service.list_for_user(
        current_user, status, patient_id, (page - 1) * size, size
    )
    return PaginatedResponse.create(
        [LabOrderShort.model_validate(o) for o in items], total, page, size
    )


@router.post("", response_model=LabOrderRead, status_code=201)
async def create_lab_order(
    body: LabOrderCreate,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    service = LabOrderService(session)
    order = await service.create(body, current_user)
    return LabOrderRead.from_orm_with_results(order)


@router.get("/{order_id}", response_model=LabOrderRead)
async def get_lab_order(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
):
    service = LabOrderService(session)
    order = await service.get_or_404(order_id)
    await service.check_access(order, current_user)
    return LabOrderRead.from_orm_with_results(order)


@router.post("/{order_id}/accept", response_model=LabOrderRead)
async def accept_order(
    order_id: UUID,
    session: DBSession,
    current_user: User = Depends(require_laboratorian()),
):
    """Laboratorian accepts the order — status: ORDERED → IN_PROGRESS."""
    service = LabOrderService(session)
    order = await service.accept(order_id, current_user)
    return LabOrderRead.from_orm_with_results(order)


@router.patch("/{order_id}/results", response_model=LabOrderRead)
async def update_results(
    order_id: UUID,
    body: LabResultsUpdate,
    session: DBSession,
    current_user: User = Depends(require_laboratorian()),
):
    """Laboratorian fills in (partial) lab results. Can be called multiple times."""
    service = LabOrderService(session)
    order = await service.update_results(order_id, body, current_user)
    return LabOrderRead.from_orm_with_results(order)


@router.post("/{order_id}/submit-results", response_model=LabOrderRead)
async def submit_results(
    order_id: UUID,
    session: DBSession,
    current_user: User = Depends(require_laboratorian()),
):
    """
    Laboratorian submits completed results.
    Validates that all requested panels are filled.
    Status: IN_PROGRESS → RESULTS_READY.
    """
    service = LabOrderService(session)
    order = await service.submit_results(order_id, current_user)
    return LabOrderRead.from_orm_with_results(order)


@router.post("/{order_id}/reopen-results", response_model=LabOrderRead)
async def reopen_results(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
    reason: str = Body(..., embed=True),
):
    """
    Laboratorian or Admin reopens submitted results for correction.
    Only allowed before a Prediction is created.
    Status: RESULTS_READY → IN_PROGRESS.
    """
    if current_user.role not in (UserRole.LABORATORIAN, UserRole.ADMIN):
        raise ForbiddenError()
    service = LabOrderService(session)
    order = await service.reopen_results(order_id, current_user)
    return LabOrderRead.from_orm_with_results(order)
