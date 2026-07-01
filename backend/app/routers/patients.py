from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, DBSession, require_doctor, require_roles
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.lab_order import LabOrderShort
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.services.lab_order_service import LabOrderService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=PaginatedResponse[PatientRead])
async def list_patients(
    session: DBSession,
    current_user: CurrentUser,
    search: str | None = Query(None, description="Search by name or MRN"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    service = PatientService(session)
    items, total = await service.search(search, (page - 1) * size, size)
    return PaginatedResponse.create(
        [PatientRead.model_validate(p) for p in items], total, page, size
    )


@router.post("", response_model=PatientRead, status_code=201)
async def create_patient(
    body: PatientCreate,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    service = PatientService(session)
    patient = await service.create(body, current_user)
    return PatientRead.model_validate(patient)


@router.get("/me", response_model=PatientRead)
async def get_my_patient_card(
    session: DBSession,
    current_user: User = Depends(require_roles(UserRole.PATIENT)),
):
    """For PATIENT role: returns their own patient card."""
    service = PatientService(session)
    patient = await service.get_for_current_user(current_user)
    return PatientRead.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
):
    service = PatientService(session)
    patient = await service.get_or_404(patient_id)
    await service.check_access(patient, current_user)
    return PatientRead.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: UUID,
    body: PatientUpdate,
    session: DBSession,
    current_user: User = Depends(require_doctor()),
):
    service = PatientService(session)
    patient = await service.update(patient_id, body)
    return PatientRead.model_validate(patient)


@router.get("/{patient_id}/lab-orders", response_model=PaginatedResponse[LabOrderShort])
async def get_patient_orders(
    patient_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    # Check patient access first
    patient_service = PatientService(session)
    patient = await patient_service.get_or_404(patient_id)
    await patient_service.check_access(patient, current_user)

    order_service = LabOrderService(session)
    items, total = await order_service.repo.list_for_user(
        user_id=current_user.id,
        user_role=current_user.role,
        status=None,
        patient_id=patient_id,
        offset=(page - 1) * size,
        limit=size,
    )
    return PaginatedResponse.create(
        [LabOrderShort.model_validate(o) for o in items], total, page, size
    )
