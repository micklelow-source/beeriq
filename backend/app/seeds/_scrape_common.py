"""Shared scraping engine behind scrape_taps.py, scrape_events.py, and
scrape_food_trucks.py -- discover a brewery's site, scrape its top
candidate pages, extract, and record via DiffService. Each caller supplies
which page types to prioritize and how to count "found" items in an
extraction, so a beer-focused run doesn't record on an events-only match
and vice versa.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable

from app.core.config import get_settings
from app.core.database import session_scope
from app.core.logging import get_logger
from app.integrations.ai import build_ai_provider
from app.integrations.fetcher import HttpxFetcher
from app.models.brewery import Brewery
from app.models.discovered_url import PageType
from app.repositories.brewery import BreweryRepository
from app.schemas.extraction import TapListExtraction
from app.services.diff import DiffService
from app.services.discovery import DiscoveryService
from app.services.extraction import ExtractionService
from app.services.scoring import ScoringService
from app.services.scrape import ScrapeService

logger = get_logger(__name__)

Counter = Callable[[TapListExtraction], int]


async def _scrape_one(
    session,
    fetcher,
    provider,
    run_settings,
    brewery: Brewery,
    *,
    page_types: dict[PageType, int],
    count: Counter,
) -> int:
    """Discover, scrape, and extract one brewery. Returns the count found
    (per ``count``), recording only when that count is non-zero."""

    discovered = await DiscoveryService(session, fetcher, run_settings).discover(brewery)
    candidates = sorted(
        (d for d in discovered if d.page_type in page_types),
        key=lambda d: (page_types[d.page_type], -d.confidence),
    )

    scrape = ScrapeService(session, fetcher)
    extractor = ExtractionService(provider)
    diff = DiffService(session)

    for candidate in candidates[:3]:
        try:
            snapshot, _ = await scrape.scrape(candidate)
        except Exception:  # unreachable / non-OK with no prior snapshot
            continue
        if not snapshot.html:
            continue
        extraction = await extractor.extract_from_html(snapshot.html)
        found = count(extraction)
        if found:
            await diff.record(candidate, extraction)
            logger.info(
                "Scraped page",
                extra={"brewery": brewery.slug, "found": found},
            )
            return found
    return 0


async def _scrape_one_isolated(
    semaphore: asyncio.Semaphore,
    fetcher,
    provider,
    run_settings,
    brewery: Brewery,
    *,
    page_types: dict[PageType, int],
    count: Counter,
) -> tuple[bool, int]:
    """Run ``_scrape_one`` under its own session so many breweries (each on a
    different external host) can be processed concurrently — a single
    AsyncSession isn't safe to share across interleaved coroutines. Returns
    ``(had_error, found)``."""

    async with semaphore:
        async with session_scope() as session:
            try:
                found = await _scrape_one(
                    session, fetcher, provider, run_settings, brewery,
                    page_types=page_types, count=count,
                )
                await ScoringService(session).compute_and_store(brewery.id)
                return False, found
            except Exception as exc:
                logger.warning(
                    "Brewery scrape failed",
                    extra={"brewery": brewery.slug, "error": str(exc)},
                )
                return True, 0


async def scrape_targets(
    targets: list[Brewery], *, page_types: dict[PageType, int], count: Counter, concurrency: int
) -> dict[str, int]:
    """Concurrently scrape a fixed list of breweries."""

    settings = get_settings()
    run_settings = settings.model_copy(
        update={"http_timeout_seconds": 8.0, "discovery_max_concurrency": 8}
    )
    provider = build_ai_provider(settings)
    stats = {"attempted": len(targets), "with_results": 0, "found": 0, "errors": 0}

    async with HttpxFetcher(run_settings) as fetcher:
        semaphore = asyncio.Semaphore(concurrency)
        results = await asyncio.gather(
            *(
                _scrape_one_isolated(
                    semaphore, fetcher, provider, run_settings, brewery,
                    page_types=page_types, count=count,
                )
                for brewery in targets
            )
        )

    for had_error, found in results:
        if had_error:
            stats["errors"] += 1
        elif found:
            stats["with_results"] += 1
            stats["found"] += found

    logger.info("Scrape complete", extra=stats)
    return stats


async def scrape_state(
    state: str,
    *,
    page_types: dict[PageType, int],
    count: Counter,
    limit: int | None = None,
    concurrency: int = 15,
) -> dict[str, int]:
    """Scrape every brewery with a website in one state."""

    async with session_scope() as session:
        repo = BreweryRepository(session)
        targets: list[Brewery] = []
        offset = 0
        while True:
            page = await repo.list_by_state(state, limit=200, offset=offset)
            if not page:
                break
            targets.extend(b for b in page if b.website)
            if len(page) < 200:
                break
            offset += 200
        if limit is not None:
            targets = targets[:limit]

    logger.info("Scraping state", extra={"state": state, "targets": len(targets)})
    return await scrape_targets(
        targets, page_types=page_types, count=count, concurrency=concurrency
    )


async def scrape_by_ids(
    brewery_ids: list[uuid.UUID],
    *,
    page_types: dict[PageType, int],
    count: Counter,
    concurrency: int = 15,
) -> dict[str, int]:
    """Scrape exactly these breweries, skipping any without a website."""

    if not brewery_ids:
        return {"attempted": 0, "with_results": 0, "found": 0, "errors": 0}

    async with session_scope() as session:
        repo = BreweryRepository(session)
        targets = [b for bid in brewery_ids if (b := await repo.get(bid)) and b.website]

    return await scrape_targets(
        targets, page_types=page_types, count=count, concurrency=concurrency
    )
