"""Generic async repository base."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[ModelT: Base]:
    """Common create/read/list/delete operations over a single model.

    Repositories hold no business logic and never commit; transaction boundaries
    are owned by the caller (the service, via ``session_scope``).
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[ModelT]:
        result = await self.session.scalars(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result)

    async def count(self) -> int:
        result = await self.session.scalar(
            select(func.count()).select_from(self.model)
        )
        return int(result or 0)

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
