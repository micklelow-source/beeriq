"""Discovered-URL repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.discovered_url import DiscoveredURL
from app.repositories.base import BaseRepository


class DiscoveredURLRepository(BaseRepository[DiscoveredURL]):
    """Queries over :class:`DiscoveredURL`."""

    model = DiscoveredURL

    async def get_by_brewery_and_url(
        self, brewery_id: uuid.UUID, url: str
    ) -> DiscoveredURL | None:
        return await self.session.scalar(
            select(DiscoveredURL).where(
                DiscoveredURL.brewery_id == brewery_id,
                DiscoveredURL.url == url,
            )
        )

    async def list_for_brewery(
        self, brewery_id: uuid.UUID
    ) -> list[DiscoveredURL]:
        result = await self.session.scalars(
            select(DiscoveredURL)
            .where(DiscoveredURL.brewery_id == brewery_id)
            .order_by(DiscoveredURL.confidence.desc())
        )
        return list(result)
