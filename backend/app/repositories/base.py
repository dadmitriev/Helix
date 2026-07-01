from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing basic CRUD operations."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        return await self.session.get(self.model, entity_id)

    async def get_all(self, offset: int = 0, limit: int = 20) -> tuple[list[ModelType], int]:
        count_q = select(func.count()).select_from(self.model)
        total = (await self.session.execute(count_q)).scalar_one()

        q = select(self.model).offset(offset).limit(limit)
        items = list((await self.session.execute(q)).scalars().all())
        return items, total

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def flush(self) -> None:
        await self.session.flush()
