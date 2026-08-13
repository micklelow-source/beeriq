"""Weekly national discovery pass: import every state's directory from Open
Brewery DB, then scrape tap lists for whichever breweries are new since the
last run.

    python -m app.seeds.discover_new_breweries
    python -m app.seeds.discover_new_breweries --state CT ME MA NH RI VT

Intentionally scoped to *new* breweries only, not a full re-scrape of the
~7,000+ already in the directory -- that would be far too slow for a weekly
run on free CI runners. Existing breweries' tap lists are refreshed by the
separate targeted scrape (see .github/workflows/weekly-tap-refresh.yml).
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.logging import get_logger
from app.seeds.directory import US_STATES, import_state_directory
from app.seeds.scrape_taps import scrape_specific_breweries

logger = get_logger(__name__)


async def discover_new_breweries(states: list[str], *, concurrency: int = 15) -> dict[str, int]:
    """Import each state's directory, then scrape tap lists for whatever
    breweries were newly inserted. Returns combined run statistics."""

    all_new_ids = []
    total_imported = 0
    for state_code in states:
        imported, new_ids = await import_state_directory(state_code)
        total_imported += imported
        all_new_ids.extend(new_ids)
        if new_ids:
            logger.info(
                "New breweries found", extra={"state": state_code, "count": len(new_ids)}
            )

    logger.info(
        "Directory refresh complete",
        extra={"states": len(states), "imported": total_imported, "new": len(all_new_ids)},
    )

    scrape_stats = await scrape_specific_breweries(all_new_ids, concurrency=concurrency)
    return {"imported": total_imported, "new_breweries": len(all_new_ids), **scrape_stats}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import all state directories and scrape tap lists for new breweries."
    )
    parser.add_argument(
        "--state",
        nargs="+",
        choices=sorted(US_STATES),
        default=sorted(US_STATES),
        help="USPS state codes to check (defaults to all 50 states + DC).",
    )
    parser.add_argument(
        "--concurrency", type=int, default=15, help="Breweries scraped in parallel."
    )
    args = parser.parse_args()

    stats = asyncio.run(discover_new_breweries(args.state, concurrency=args.concurrency))
    logger.info(
        "Done: %d new breweries (of %d imported), %d/%d scraped with taps, %d beers, %d errors",
        stats["new_breweries"],
        stats["imported"],
        stats["with_taps"],
        stats["attempted"],
        stats["beers"],
        stats["errors"],
    )


if __name__ == "__main__":
    main()
