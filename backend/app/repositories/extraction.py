"""Extraction repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.discovered_url import DiscoveredURL
from app.models.extraction import Extraction
from app.repositories.base import BaseRepository


class ExtractionRepository(BaseRepository[Extraction]):
    """Queries over :class:`Extraction`."""

    model = Extraction

    async def latest_for_url(
        self, discovered_url_id: uuid.UUID
    ) -> Extraction | None:
        """Return the most recent stored extraction for a discovered URL."""

        return await self.session.scalar(
            select(Extraction)
            .where(Extraction.discovered_url_id == discovered_url_id)
            .order_by(Extraction.created_at.desc())
            .limit(1)
        )

    async def count_for_brewery(self, brewery_id: uuid.UUID) -> int:
        """Count all extractions across a brewery's discovered URLs."""

        result = await self.session.scalar(
            select(func.count())
            .select_from(Extraction)
            .join(DiscoveredURL, Extraction.discovered_url_id == DiscoveredURL.id)
            .where(DiscoveredURL.brewery_id == brewery_id)
        )
        return int(result or 0)
