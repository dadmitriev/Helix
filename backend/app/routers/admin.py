from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DBSession, require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.lab_order import LabOrder
from app.schemas.common import PaginatedResponse
from sqlalchemy import select, func

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

router = APIRouter(prefix="/admin", tags=["Admin"])


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: UUID | None
    action: str
    entity_type: str | None
    entity_id: UUID | None
    details: dict | None
    ip_address: str | None
    timestamp: datetime


class SystemStats(BaseModel):
    total_users: int
    total_patients: int
    orders_by_status: dict[str, int]


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogRead])
async def get_audit_logs(
    session: DBSession,
    _: User = Depends(require_admin()),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    base = select(AuditLog)
    if action:
        base = base.where(AuditLog.action == action)
    base = base.order_by(AuditLog.timestamp.desc())

    count_q = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_q)).scalar_one()

    q = base.offset((page - 1) * size).limit(size)
    logs = list((await session.execute(q)).scalars().all())

    return PaginatedResponse.create(
        [AuditLogRead.model_validate(log) for log in logs], total, page, size
    )


@router.get("/stats", response_model=SystemStats)
async def get_stats(
    session: DBSession,
    _: User = Depends(require_admin()),
):
    from app.models.user import User
    from app.models.patient import Patient

    total_users = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    total_patients = (await session.execute(select(func.count()).select_from(Patient))).scalar_one()

    status_rows = (await session.execute(
        select(LabOrder.status, func.count()).group_by(LabOrder.status)
    )).all()
    orders_by_status = {row[0].value: row[1] for row in status_rows}

    return SystemStats(
        total_users=total_users,
        total_patients=total_patients,
        orders_by_status=orders_by_status,
    )
