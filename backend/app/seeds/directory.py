"""Import a state's brewery directory from Open Brewery DB.

    python -m app.seeds.directory --state NH
    python -m app.seeds.directory --state ME VT MA RI CT

Idempotent (upsert by slug). Records with an invalid website URL are imported
without a website rather than skipped, so directory coverage stays complete.
"""

from __future__ import annotations

import argparse
import asyncio

from pydantic import ValidationError

from app.core.database import session_scope
from app.core.logging import get_logger
from app.integrations.openbrewerydb import DirectoryBrewery, OpenBreweryDBClient
from app.schemas.brewery import BreweryCreate
from app.services.brewery import BreweryService

logger = get_logger(__name__)

# Open Brewery DB state slug, keyed by USPS code — New England for now (spec's
# initial coverage area); expand as the directory grows to other regions.
NEW_ENGLAND_STATES: dict[str, str] = {
    "CT": "connecticut",
    "ME": "maine",
    "MA": "massachusetts",
    "NH": "new_hampshire",
    "RI": "rhode_island",
    "VT": "vermont",
}


def _to_payload(record: DirectoryBrewery, *, drop_website: bool = False) -> BreweryCreate:
    return BreweryCreate(
        name=record.name,
        website=None if drop_website else record.website,
        brewery_type=record.brewery_type,
        city=record.city,
        state=record.state_code,
        latitude=record.latitude,
        longitude=record.longitude,
    )


async def import_state_directory(state_code: str) -> int:
    """Fetch and upsert all active breweries for one state. Returns count imported."""

    state_slug = NEW_ENGLAND_STATES[state_code]
    async with OpenBreweryDBClient() as client:
        records = await client.breweries_by_state(state_slug, state_code)

    imported = 0
    async with session_scope() as session:
        service = BreweryService(session)
        for record in records:
            try:
                payload = _to_payload(record)
            except ValidationError:
                # Almost always a malformed website_url — import without it.
                payload = _to_payload(record, drop_website=True)
            brewery = await service.upsert_by_slug(payload)
            # Backfill brewery_type on records imported before this column existed.
            if brewery.brewery_type != record.brewery_type:
                brewery.brewery_type = record.brewery_type
            imported += 1

    logger.info("Directory import complete", extra={"state": state_code, "imported": imported})
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import brewery directories from Open Brewery DB.")
    parser.add_argument(
        "--state",
        nargs="+",
        choices=sorted(NEW_ENGLAND_STATES),
        default=["NH"],
        help="One or more USPS state codes to import.",
    )
    args = parser.parse_args()

    async def run() -> None:
        for state_code in args.state:
            count = await import_state_directory(state_code)
            logger.info("Imported %d %s breweries from Open Brewery DB", count, state_code)

    asyncio.run(run())


if __name__ == "__main__":
    main()
