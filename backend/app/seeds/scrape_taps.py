"""Scrape real tap lists from brewery websites (spec §1–4).

Runs the full pipeline against each brewery's live site: discover tap/menu pages
(by URL *and* by content markers like "what's on tap" / "current offerings"),
scrape them, extract beers with the configured AI provider (set
``BREWIQ_AI_PROVIDER=heuristic`` for the keyless parser), diff against the prior
tap list, and recompute the score.

    python -m app.seeds.scrape_taps            # all NH breweries with a website
    python -m app.seeds.scrape_taps --limit 25 # first 25 only
    python -m app.seeds.scrape_taps --state NH
    python -m app.seeds.scrape_taps --state CT ME MA NH RI VT
    python -m app.seeds.scrape_taps --state ALL # every state in the directory

Note: Open Brewery DB has no tap lists — these come only from scraping. Sites
that render their tap list with JavaScript won't yield beers via httpx; those
need the Playwright fetcher (spec §2) and/or the Anthropic provider. A brewery
already holding a richer, manually-curated extraction is never overwritten by
an empty automated result — ``diff.record`` is only called when beers are
actually found.
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.config import get_settings
from app.core.database import session_scope
from app.core.logging import get_logger
from app.integrations.ai import build_ai_provider
from app.integrations.fetcher import HttpxFetcher
from app.models.brewery import Brewery
from app.models.discovered_url import PageType
from app.repositories.brewery import BreweryRepository
from app.seeds.directory import US_STATES
from app.services.diff import DiffService
from app.services.discovery import DiscoveryService
from app.services.extraction import ExtractionService
from app.services.scoring import ScoringService
from app.services.scrape import ScrapeService

logger = get_logger(__name__)

# Page types worth scraping for a tap list, best first.
_SCRAPE_ORDER = {PageType.TAP: 0, PageType.BEER: 1, PageType.MENU: 2}


async def _scrape_one(session, fetcher, provider, run_settings, brewery: Brewery) -> int:
    """Discover, scrape, and extract one brewery. Returns beers found."""

    discovered = await DiscoveryService(session, fetcher, run_settings).discover(brewery)
    candidates = sorted(
        (d for d in discovered if d.page_type in _SCRAPE_ORDER),
        key=lambda d: (_SCRAPE_ORDER[d.page_type], -d.confidence),
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
        if extraction.beers:
            await diff.record(candidate, extraction)
            logger.info(
                "Scraped tap list",
                extra={"brewery": brewery.slug, "beers": len(extraction.beers)},
            )
            return len(extraction.beers)
    return 0


async def _scrape_one_isolated(
    semaphore: asyncio.Semaphore, fetcher, provider, run_settings, brewery: Brewery
) -> tuple[bool, int]:
    """Run ``_scrape_one`` under its own session so many breweries (each on a
    different external host) can be processed concurrently — a single
    AsyncSession isn't safe to share across interleaved coroutines. Returns
    ``(had_error, beers_found)``."""

    async with semaphore:
        async with session_scope() as session:
            try:
                found = await _scrape_one(session, fetcher, provider, run_settings, brewery)
                await ScoringService(session).compute_and_store(brewery.id)
                return False, found
            except Exception as exc:
                logger.warning(
                    "Brewery scrape failed",
                    extra={"brewery": brewery.slug, "error": str(exc)},
                )
                return True, 0


async def scrape_taps(
    *, state: str = "NH", limit: int | None = None, concurrency: int = 15
) -> dict[str, int]:
    """Scrape tap lists for a state's breweries, or every state if ``state="ALL"``.
    Breweries are processed concurrently (bounded by ``concurrency``) since
    each lives on a different external host — safe and far faster than one
    at a time. Returns run statistics."""

    if state == "ALL":
        totals = {"attempted": 0, "with_taps": 0, "beers": 0, "errors": 0}
        for state_code in sorted(US_STATES):
            stats = await scrape_taps(state=state_code, limit=limit, concurrency=concurrency)
            for key in totals:
                totals[key] += stats[key]
        return totals

    settings = get_settings()
    run_settings = settings.model_copy(
        update={"http_timeout_seconds": 8.0, "discovery_max_concurrency": 8}
    )
    provider = build_ai_provider(settings)
    stats = {"attempted": 0, "with_taps": 0, "beers": 0, "errors": 0}

    async with HttpxFetcher(run_settings) as fetcher:
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

        logger.info("Scraping tap lists", extra={"state": state, "targets": len(targets)})
        semaphore = asyncio.Semaphore(concurrency)
        results = await asyncio.gather(
            *(
                _scrape_one_isolated(semaphore, fetcher, provider, run_settings, brewery)
                for brewery in targets
            )
        )

    stats["attempted"] = len(targets)
    for had_error, found in results:
        if had_error:
            stats["errors"] += 1
        elif found:
            stats["with_taps"] += 1
            stats["beers"] += found

    logger.info("Scrape complete", extra=stats)
    return stats


async def _scrape_many(states: list[str], *, limit: int | None, concurrency: int) -> dict[str, int]:
    if states == ["ALL"]:
        return await scrape_taps(state="ALL", limit=limit, concurrency=concurrency)

    totals = {"attempted": 0, "with_taps": 0, "beers": 0, "errors": 0}
    for state_code in states:
        stats = await scrape_taps(state=state_code, limit=limit, concurrency=concurrency)
        for key in totals:
            totals[key] += stats[key]
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape brewery tap lists.")
    parser.add_argument(
        "--state",
        nargs="+",
        default=["NH"],
        help='One or more USPS state codes, or "ALL" for every state.',
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--concurrency", type=int, default=15, help="Breweries scraped in parallel."
    )
    args = parser.parse_args()
    stats = asyncio.run(
        _scrape_many(args.state, limit=args.limit, concurrency=args.concurrency)
    )
    logger.info(
        "Done: %d/%d breweries with taps, %d beers, %d errors",
        stats["with_taps"],
        stats["attempted"],
        stats["beers"],
        stats["errors"],
    )


if __name__ == "__main__":
    main()
