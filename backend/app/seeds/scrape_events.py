"""Scrape brewery events (beer tastings, festivals, trivia nights, ...) using
the heuristic events parser (app.services.event_parser) -- same discover ->
scrape -> extract -> diff pipeline as scrape_taps.py, but targeting
events/calendar pages and recording only when events are actually found.

    python -m app.seeds.scrape_events            # all NH breweries
    python -m app.seeds.scrape_events --state CT ME MA NH RI VT
    python -m app.seeds.scrape_events --state ALL

Run on its own schedule, separate from the tap-list scrape (see
.github/workflows/weekly-events-refresh.yml) -- events churn on a different
cadence than tap lists, and keeping the jobs independent means a failure in
one doesn't block the other.
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.logging import get_logger
from app.models.discovered_url import PageType
from app.schemas.extraction import TapListExtraction
from app.seeds._scrape_common import scrape_state
from app.seeds.directory import US_STATES

logger = get_logger(__name__)

# Events pages first; tap/beer/menu pages are a fallback since some
# breweries list an event or two alongside their tap list.
_PAGE_TYPES = {PageType.EVENTS: 0, PageType.MENU: 1, PageType.TAP: 2, PageType.BEER: 3}


def _count_events(extraction: TapListExtraction) -> int:
    return len(extraction.events)


async def scrape_events(
    *, state: str = "NH", limit: int | None = None, concurrency: int = 15
) -> dict[str, int]:
    if state == "ALL":
        totals = {"attempted": 0, "with_events": 0, "events": 0, "errors": 0}
        for state_code in sorted(US_STATES):
            stats = await scrape_events(state=state_code, limit=limit, concurrency=concurrency)
            for key in totals:
                totals[key] += stats[key]
        return totals

    raw = await scrape_state(
        state, page_types=_PAGE_TYPES, count=_count_events, limit=limit, concurrency=concurrency
    )
    return {
        "attempted": raw["attempted"],
        "with_events": raw["with_results"],
        "events": raw["found"],
        "errors": raw["errors"],
    }


async def _scrape_many(states: list[str], *, limit: int | None, concurrency: int) -> dict[str, int]:
    if states == ["ALL"]:
        return await scrape_events(state="ALL", limit=limit, concurrency=concurrency)

    totals = {"attempted": 0, "with_events": 0, "events": 0, "errors": 0}
    for state_code in states:
        stats = await scrape_events(state=state_code, limit=limit, concurrency=concurrency)
        for key in totals:
            totals[key] += stats[key]
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape brewery events.")
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
        "Done: %d/%d breweries with events, %d events, %d errors",
        stats["with_events"],
        stats["attempted"],
        stats["events"],
        stats["errors"],
    )


if __name__ == "__main__":
    main()
