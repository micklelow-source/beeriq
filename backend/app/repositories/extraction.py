"""Extraction repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

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
