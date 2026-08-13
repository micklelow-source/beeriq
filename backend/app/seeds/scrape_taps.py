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

Events and food trucks are scraped separately (see scrape_events.py and
scrape_food_trucks.py) so each can run on its own schedule.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid

from app.core.logging import get_logger
from app.models.discovered_url import PageType
from app.schemas.extraction import TapListExtraction
from app.seeds._scrape_common import scrape_by_ids, scrape_state
from app.seeds.directory import US_STATES

logger = get_logger(__name__)

# Page types worth scraping for a tap list, best first.
_PAGE_TYPES = {PageType.TAP: 0, PageType.BEER: 1, PageType.MENU: 2}


def _count_beers(extraction: TapListExtraction) -> int:
    return len(extraction.beers)


def _to_beer_stats(raw: dict[str, int]) -> dict[str, int]:
    return {
        "attempted": raw["attempted"],
        "with_taps": raw["with_results"],
        "beers": raw["found"],
        "errors": raw["errors"],
    }


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

    raw = await scrape_state(
        state, page_types=_PAGE_TYPES, count=_count_beers, limit=limit, concurrency=concurrency
    )
    return _to_beer_stats(raw)


async def scrape_specific_breweries(
    brewery_ids: list[uuid.UUID], *, concurrency: int = 15
) -> dict[str, int]:
    """Scrape tap lists for exactly these breweries (e.g. ones a directory
    refresh just discovered), skipping any without a website."""

    raw = await scrape_by_ids(
        brewery_ids, page_types=_PAGE_TYPES, count=_count_beers, concurrency=concurrency
    )
    return _to_beer_stats(raw)


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
