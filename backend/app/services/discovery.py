"""Website Discovery Engine (spec §1).

Given a brewery's website, discover tap/beer/menu/events/food-truck pages by:

1. Probing well-known candidate paths (``/tap``, ``/beers``, ``/menu`` …).
2. Fetching the home page and classifying its internal navigation links.

Results are persisted as :class:`DiscoveredURL` rows (idempotent upsert, keeping
the highest-confidence classification).
"""

from __future__ import annotations

import asyncio
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations.fetcher import Fetcher, FetchRequest, FetchResponse
from app.models.brewery import Brewery
from app.models.discovered_url import DiscoveredURL, PageType
from app.repositories.discovered_url import DiscoveredURLRepository
from app.services.classifier import (
    CANDIDATE_PATHS,
    classify_url,
    content_tap_confidence,
)

logger = get_logger(__name__)


class _LinkExtractor(HTMLParser):
    """Collect ``(href, anchor_text)`` pairs from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._text_parts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._current_href = href
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            self.links.append((self._current_href, "".join(self._text_parts).strip()))
            self._current_href = None
            self._text_parts = []


def _normalize_base(website: str) -> str:
    """Return the website with a trailing slash and no path, for joining."""

    parsed = urlparse(website)
    scheme = parsed.scheme or "https"
    return f"{scheme}://{parsed.netloc or parsed.path}".rstrip("/") + "/"


class DiscoveryService:
    """Discovers and persists candidate URLs for a brewery."""

    def __init__(
        self,
        session: AsyncSession,
        fetcher: Fetcher,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.fetcher = fetcher
        self.settings = settings or get_settings()
        self.repo = DiscoveredURLRepository(session)

    async def discover(self, brewery: Brewery) -> list[DiscoveredURL]:
        """Discover URLs for ``brewery`` and persist the results.

        Raises :class:`ValueError` if the brewery has no website configured.
        """

        if not brewery.website:
            raise ValueError(f"Brewery {brewery.slug!r} has no website to discover")

        base = _normalize_base(brewery.website)
        candidates = self._collect_candidates(base)

        home_links = await self._fetch_home_links(base)
        candidates.update(home_links)
        # Probe the home page too — some breweries list taps on it, detected by
        # content markers below.
        candidates.add(base)

        logger.info(
            "Discovering brewery site",
            extra={"brewery": brewery.slug, "candidate_count": len(candidates)},
        )

        # Probe every candidate concurrently, bounded by configured concurrency.
        semaphore = asyncio.Semaphore(self.settings.discovery_max_concurrency)
        results = await asyncio.gather(
            *(self._probe(url, semaphore) for url in candidates)
        )

        discovered: list[DiscoveredURL] = []
        for url, response in results:
            if response is None or not response.ok:
                continue
            page_type, confidence = classify_url(url)
            # Promote to TAP when the page body reads like a tap list, even if the
            # URL is generic (e.g. "/menu" or the home page).
            content_conf = content_tap_confidence(response.text)
            if content_conf > confidence:
                page_type, confidence = PageType.TAP, content_conf
            if confidence <= 0:
                continue
            record = await self._upsert(brewery, url, page_type, confidence)
            if record is not None:
                discovered.append(record)
        return discovered

    def _collect_candidates(self, base: str) -> set[str]:
        """Build the initial candidate set from well-known paths."""

        return {urljoin(base, path) for path in CANDIDATE_PATHS}

    async def _fetch_home_links(self, base: str) -> set[str]:
        """Fetch the home page and return classifiable, same-host links."""

        try:
            response = await self.fetcher.fetch(FetchRequest(url=base))
        except Exception as exc:  # network failures must not abort discovery
            logger.warning("Home page fetch failed", extra={"url": base, "error": str(exc)})
            return set()

        if not response.ok:
            return set()

        extractor = _LinkExtractor()
        extractor.feed(response.text)

        base_host = urlparse(base).netloc
        found: set[str] = set()
        for href, text in extractor.links:
            absolute = urljoin(base, href)
            if urlparse(absolute).netloc != base_host:
                continue  # ignore off-site links (social media, maps, …)
            _, confidence = classify_url(absolute, link_text=text)
            if confidence > 0:
                found.add(absolute.split("#")[0])
        return found

    async def _probe(
        self, url: str, semaphore: asyncio.Semaphore
    ) -> tuple[str, FetchResponse | None]:
        """Return ``(url, response)`` — the fetched response, or None on failure."""

        async with semaphore:
            try:
                response = await self.fetcher.fetch(FetchRequest(url=url))
            except Exception as exc:
                logger.debug("Probe failed", extra={"url": url, "error": str(exc)})
                return url, None
            return url, response

    async def _upsert(
        self,
        brewery: Brewery,
        url: str,
        page_type: PageType,
        confidence: float,
    ) -> DiscoveredURL | None:
        """Insert a new discovered URL or upgrade an existing lower-confidence one."""

        existing = await self.repo.get_by_brewery_and_url(brewery.id, url)
        if existing is None:
            return await self.repo.add(
                DiscoveredURL(
                    brewery_id=brewery.id,
                    url=url,
                    page_type=page_type,
                    confidence=confidence,
                )
            )
        if confidence > existing.confidence:
            existing.page_type = page_type
            existing.confidence = confidence
            await self.session.flush()
        return existing
