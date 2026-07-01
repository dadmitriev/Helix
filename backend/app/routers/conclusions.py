from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DBSession, require_doctor
from app.models.user import User
from app.schemas.conclusion import ConclusionCreate, ConclusionRead, ConclusionUpdate
from app.services.conclusion_service import ConclusionService

router = APIRouter(prefix="/lab-orders", tags=["Conclusions"])


@router.post("/{order_id}/conclusion", response_model=ConclusionRead, status_code=201)
async def create_conclusion(
    order_id: UUID,
    body: ConclusionCreate,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    service = ConclusionService(session)
    conclusion = await service.create(order_id, body, current_user)
    return ConclusionRead.model_validate(conclusion)


@router.patch("/{order_id}/conclusion", response_model=ConclusionRead)
async def update_conclusion(
    order_id: UUID,
    body: ConclusionUpdate,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    service = ConclusionService(session)
    conclusion = await service.update(order_id, body, current_user)
    return ConclusionRead.model_validate(conclusion)


@router.post("/{order_id}/conclusion/send", response_model=ConclusionRead)
async def send_conclusion(
    order_id: UUID,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    """
    Doctor finalizes and sends the conclusion to the patient.
    Status: DRAFT → SENT. LabOrder status → CONCLUDED.
    """
    service = ConclusionService(session)
    conclusion = await service.send(order_id, current_user)
    return ConclusionRead.model_validate(conclusion)


@router.get("/{order_id}/conclusion", response_model=ConclusionRead | None)
async def get_conclusion(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
):
    service = ConclusionService(session)
    conclusion = await service.get_for_order(order_id, current_user)
    if conclusion is None:
        return None
    return ConclusionRead.model_validate(conclusion)
