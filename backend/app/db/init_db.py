"""
Database seeding — runs once at startup.
Creates the first ADMIN user if no users exist.
"""

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def init_db() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # Already seeded

        logger.info("No users found — creating initial admin user...")

        admin = User(
            email=settings.FIRST_ADMIN_EMAIL,
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            first_name=settings.FIRST_ADMIN_FIRST_NAME,
            last_name=settings.FIRST_ADMIN_LAST_NAME,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        logger.info("Admin user created: %s", settings.FIRST_ADMIN_EMAIL)
