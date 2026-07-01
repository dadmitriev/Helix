from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, DBSession, require_admin, require_roles
from app.core.exceptions import ForbiddenError
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserRead])
async def list_users(
    session: DBSession,
    _: User = Depends(require_admin()),
    role: UserRole | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    service = UserService(session)
    offset = (page - 1) * size
    items, total = await service.list_users(role, is_active, offset, size)
    return PaginatedResponse.create(
        [UserRead.model_validate(u) for u in items], total, page, size
    )


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    body: UserCreate,
    session: DBSession,
    _: User = Depends(require_admin()),
):
    service = UserService(session)
    user = await service.create(body)
    return UserRead.model_validate(user)


@router.get("/doctors", response_model=list[UserRead])
async def list_doctors(
    session: DBSession,
    current_user: CurrentUser,
):
    """Available to all authenticated users (for order assignment UI)."""
    service = UserService(session)
    doctors = await service.list_doctors()
    return [UserRead.model_validate(d) for d in doctors]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
):
    # User can view themselves; admin can view anyone
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise ForbiddenError()
    service = UserService(session)
    user = await service.get_or_404(user_id)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    session: DBSession,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise ForbiddenError()
    service = UserService(session)
    user = await service.update(user_id, body)
    return UserRead.model_validate(user)


@router.patch("/{user_id}/toggle-active", response_model=UserRead)
async def toggle_active(
    user_id: UUID,
    session: DBSession,
    _: User = Depends(require_admin()),
):
    service = UserService(session)
    user = await service.toggle_active(user_id)
    return UserRead.model_validate(user)
