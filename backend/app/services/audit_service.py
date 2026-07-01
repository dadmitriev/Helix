"""
Audit logging service. Writes AuditLog records asynchronously
without blocking the main request/response cycle.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        action: str,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        try:
            entry = AuditLog(
                action=action,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.session.add(entry)
            await self.session.flush()
        except Exception as exc:
            # Audit failures must never break business logic
            logger.warning("Failed to write audit log [%s]: %s", action, exc)
