"""Brewery-score repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.brewery_score import BreweryScore
from app.repositories.base import BaseRepository


class BreweryScoreRepository(BaseRepository[BreweryScore]):
    """Queries over :class:`BreweryScore`."""

    model = BreweryScore

    async def latest_for_brewery(
        self, brewery_id: uuid.UUID
    ) -> BreweryScore | None:
        """Return the most recent stored score for a brewery, if any."""

        return await self.session.scalar(
            select(BreweryScore)
            .where(BreweryScore.brewery_id == brewery_id)
            .order_by(BreweryScore.created_at.desc())
            .limit(1)
        )
