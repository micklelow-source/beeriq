"""Page-snapshot repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.page_snapshot import PageSnapshot
from app.repositories.base import BaseRepository


class PageSnapshotRepository(BaseRepository[PageSnapshot]):
    """Queries over :class:`PageSnapshot`."""

    model = PageSnapshot

    async def latest_for_url(
        self, discovered_url_id: uuid.UUID
    ) -> PageSnapshot | None:
        """Return the most recent snapshot for a discovered URL, if any."""

        return await self.session.scalar(
            select(PageSnapshot)
            .where(PageSnapshot.discovered_url_id == discovered_url_id)
            .order_by(PageSnapshot.created_at.desc())
            .limit(1)
        )
