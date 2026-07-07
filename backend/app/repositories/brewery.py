"""Brewery repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.brewery import Brewery
from app.repositories.base import BaseRepository


class BreweryRepository(BaseRepository[Brewery]):
    """Queries over :class:`Brewery`."""

    model = Brewery

    async def get_by_slug(self, slug: str) -> Brewery | None:
        return await self.session.scalar(
            select(Brewery).where(Brewery.slug == slug)
        )

    async def list_by_state(
        self, state: str, *, limit: int = 50, offset: int = 0
    ) -> list[Brewery]:
        result = await self.session.scalars(
            select(Brewery)
            .where(Brewery.state == state.upper())
            .order_by(Brewery.name)
            .limit(limit)
            .offset(offset)
        )
        return list(result)

    async def count_by_state(self) -> list[tuple[str, int]]:
        """Return ``(state, count)`` pairs for every state with breweries."""

        result = await self.session.execute(
            select(Brewery.state, func.count())
            .where(Brewery.state.is_not(None))
            .group_by(Brewery.state)
            .order_by(Brewery.state)
        )
        return [(state, count) for state, count in result.all()]
