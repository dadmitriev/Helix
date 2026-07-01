from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        q = select(User).where(User.email == email)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_by_role(
        self, role: UserRole, offset: int = 0, limit: int = 20
    ) -> tuple[list[User], int]:
        from sqlalchemy import func

        count_q = select(func.count()).select_from(User).where(User.role == role)
        total = (await self.session.execute(count_q)).scalar_one()

        q = select(User).where(User.role == role).offset(offset).limit(limit)
        users = list((await self.session.execute(q)).scalars().all())
        return users, total

    async def list_filtered(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        from sqlalchemy import func

        filters = []
        if role is not None:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)

        base = select(User)
        if filters:
            base = base.where(*filters)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        q = base.offset(offset).limit(limit)
        users = list((await self.session.execute(q)).scalars().all())
        return users, total

    async def email_exists(self, email: str, exclude_id: UUID | None = None) -> bool:
        q = select(User.id).where(User.email == email)
        if exclude_id:
            q = q.where(User.id != exclude_id)
        result = await self.session.execute(q)
        return result.scalar_one_or_none() is not None
