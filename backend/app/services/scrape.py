"""Scrape service (spec §2, partial).

Fetches a discovered URL, computes a content hash, and stores a
:class:`PageSnapshot`. Conditional requests (ETag / Last-Modified) and hash
comparison against the previous snapshot provide change detection, which the diff
engine (spec §4) will build on. The Playwright-backed fetcher slots in behind the
same :class:`Fetcher` interface without touching this code.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.utils import content_hash
from app.integrations.fetcher import Fetcher, FetchRequest
from app.models.discovered_url import DiscoveredURL
from app.models.page_snapshot import PageSnapshot
from app.repositories.page_snapshot import PageSnapshotRepository

logger = get_logger(__name__)


class ScrapeService:
    """Fetches and archives snapshots of discovered URLs."""

    def __init__(self, session: AsyncSession, fetcher: Fetcher) -> None:
        self.session = session
        self.fetcher = fetcher
        self.repo = PageSnapshotRepository(session)

    async def scrape(self, discovered: DiscoveredURL) -> tuple[PageSnapshot, bool]:
        """Fetch ``discovered`` and store a snapshot.

        Returns ``(snapshot, changed)`` where ``changed`` is ``True`` when the
        content differs from the previous snapshot. A ``304 Not Modified`` short-
        circuits to the previous snapshot marked unchanged.

        Raises :class:`RuntimeError` if the URL cannot be fetched successfully and
        no prior snapshot exists to fall back on.
        """

        previous = await self.repo.latest_for_url(discovered.id)
        request = FetchRequest(
            url=discovered.url,
            etag=previous.etag if previous else None,
            last_modified=previous.last_modified if previous else None,
        )
        response = await self.fetcher.fetch(request)

        if response.not_modified and previous is not None:
            logger.info("Page unchanged (304)", extra={"url": discovered.url})
            return previous, False

        if not response.ok:
            if previous is not None:
                logger.warning(
                    "Fetch not OK; keeping previous snapshot",
                    extra={"url": discovered.url, "status": response.status_code},
                )
                return previous, False
            raise RuntimeError(
                f"Failed to fetch {discovered.url!r}: HTTP {response.status_code}"
            )

        new_hash = content_hash(response.text)
        changed = previous is None or previous.content_hash != new_hash

        snapshot = await self.repo.add(
            PageSnapshot(
                discovered_url_id=discovered.id,
                status_code=response.status_code,
                content_hash=new_hash,
                html=response.text,
                etag=response.etag,
                last_modified=response.last_modified,
            )
        )
        logger.info(
            "Stored snapshot",
            extra={"url": discovered.url, "changed": changed, "hash": new_hash[:8]},
        )
        return snapshot, changed
