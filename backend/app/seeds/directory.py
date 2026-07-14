"""Import a state's brewery directory from Open Brewery DB.

    python -m app.seeds.directory --state NH
    python -m app.seeds.directory --state NY NJ PA

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

# Open Brewery DB state slug, keyed by USPS code — all 50 states plus DC.
US_STATES: dict[str, str] = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas",
    "CA": "california", "CO": "colorado", "CT": "connecticut", "DE": "delaware",
    "DC": "district_of_columbia",
    "FL": "florida", "GA": "georgia", "HI": "hawaii", "ID": "idaho",
    "IL": "illinois", "IN": "indiana", "IA": "iowa", "KS": "kansas",
    "KY": "kentucky", "LA": "louisiana", "ME": "maine", "MD": "maryland",
    "MA": "massachusetts", "MI": "michigan", "MN": "minnesota", "MS": "mississippi",
    "MO": "missouri", "MT": "montana", "NE": "nebraska", "NV": "nevada",
    "NH": "new_hampshire", "NJ": "new_jersey", "NM": "new_mexico", "NY": "new_york",
    "NC": "north_carolina", "ND": "north_dakota", "OH": "ohio", "OK": "oklahoma",
    "OR": "oregon", "PA": "pennsylvania", "RI": "rhode_island", "SC": "south_carolina",
    "SD": "south_dakota", "TN": "tennessee", "TX": "texas", "UT": "utah",
    "VT": "vermont", "VA": "virginia", "WA": "washington", "WV": "west_virginia",
    "WI": "wisconsin", "WY": "wyoming",
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

    state_slug = US_STATES[state_code]
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
        choices=sorted(US_STATES),
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
