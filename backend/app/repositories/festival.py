"""Festival repository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models.festival import Festival
from app.repositories.base import BaseRepository


class FestivalRepository(BaseRepository[Festival]):
    """Queries over :class:`Festival`."""

    model = Festival

    async def get_by_slug(self, slug: str) -> Festival | None:
        return await self.session.scalar(select(Festival).where(Festival.slug == slug))

    async def list_upcoming(
        self, *, on_or_after: date, limit: int = 200, offset: int = 0
    ) -> list[Festival]:
        """Return festivals happening on/after ``on_or_after``, soonest first.

        Undated festivals (``event_date is None``) sort last rather than
        being dropped, since a curated listing may still be worth surfacing
        even without a confirmed date.
        """

        result = await self.session.scalars(
            select(Festival)
            .where((Festival.event_date >= on_or_after) | (Festival.event_date.is_(None)))
            .order_by(Festival.event_date.is_(None), Festival.event_date, Festival.name)
            .limit(limit)
            .offset(offset)
        )
        return list(result)
