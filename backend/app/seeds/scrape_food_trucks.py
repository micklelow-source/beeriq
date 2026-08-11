"""Scrape brewery food-truck schedules using the heuristic food-truck parser
(app.services.food_truck_parser) -- same discover -> scrape -> extract ->
diff pipeline as scrape_taps.py, but targeting food-truck/events pages and
recording only when trucks are actually found.

    python -m app.seeds.scrape_food_trucks            # all NH breweries
    python -m app.seeds.scrape_food_trucks --state CT ME MA NH RI VT
    python -m app.seeds.scrape_food_trucks --state ALL

Run on its own weekly schedule (see
.github/workflows/weekly-foodtrucks-refresh.yml), independent of the
tap-list and events jobs.
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

# Food-truck pages first; a truck schedule often lives on the same page as
# events, so that's the fallback, then tap/menu as a last resort.
_PAGE_TYPES = {PageType.FOOD_TRUCK: 0, PageType.EVENTS: 1, PageType.MENU: 2, PageType.TAP: 3}


def _count_trucks(extraction: TapListExtraction) -> int:
    return len(extraction.food_trucks)


async def scrape_food_trucks(
    *, state: str = "NH", limit: int | None = None, concurrency: int = 15
) -> dict[str, int]:
    if state == "ALL":
        totals = {"attempted": 0, "with_trucks": 0, "trucks": 0, "errors": 0}
        for state_code in sorted(US_STATES):
            stats = await scrape_food_trucks(
                state=state_code, limit=limit, concurrency=concurrency
            )
            for key in totals:
                totals[key] += stats[key]
        return totals

    raw = await scrape_state(
        state, page_types=_PAGE_TYPES, count=_count_trucks, limit=limit, concurrency=concurrency
    )
    return {
        "attempted": raw["attempted"],
        "with_trucks": raw["with_results"],
        "trucks": raw["found"],
        "errors": raw["errors"],
    }


async def _scrape_many(states: list[str], *, limit: int | None, concurrency: int) -> dict[str, int]:
    if states == ["ALL"]:
        return await scrape_food_trucks(state="ALL", limit=limit, concurrency=concurrency)

    totals = {"attempted": 0, "with_trucks": 0, "trucks": 0, "errors": 0}
    for state_code in states:
        stats = await scrape_food_trucks(state=state_code, limit=limit, concurrency=concurrency)
        for key in totals:
            totals[key] += stats[key]
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape brewery food-truck schedules.")
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
        "Done: %d/%d breweries with food trucks, %d trucks, %d errors",
        stats["with_trucks"],
        stats["attempted"],
        stats["trucks"],
        stats["errors"],
    )


if __name__ == "__main__":
    main()
