"""Change-event repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select

from app.models.change_event import ChangeEvent, ChangeEventType
from app.repositories.base import BaseRepository


class ChangeEventRepository(BaseRepository[ChangeEvent]):
    """Queries over :class:`ChangeEvent`."""

    model = ChangeEvent

    async def list_for_brewery(
        self, brewery_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ChangeEvent]:
        """Return a brewery's change events, newest first."""

        result = await self.session.scalars(
            select(ChangeEvent)
            .where(ChangeEvent.brewery_id == brewery_id)
            .order_by(ChangeEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result)

    async def count_for_brewery(self, brewery_id: uuid.UUID) -> int:
        result = await self.session.scalar(
            select(func.count())
            .select_from(ChangeEvent)
            .where(ChangeEvent.brewery_id == brewery_id)
        )
        return int(result or 0)

    async def count_recent_by_type(
        self,
        brewery_id: uuid.UUID,
        event_types: Sequence[ChangeEventType],
        since: datetime,
    ) -> int:
        """Count a brewery's events of the given types since ``since``."""

        result = await self.session.scalar(
            select(func.count())
            .select_from(ChangeEvent)
            .where(
                ChangeEvent.brewery_id == brewery_id,
                ChangeEvent.event_type.in_(event_types),
                ChangeEvent.created_at >= since,
            )
        )
        return int(result or 0)
