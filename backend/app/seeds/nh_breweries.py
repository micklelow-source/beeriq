"""Seed importer for New Hampshire breweries.

Run as a module against a database that already has the schema (``alembic upgrade
head``)::

    python -m app.seeds.nh_breweries

The import is idempotent — re-running it will not create duplicates.
"""

from __future__ import annotations

import asyncio

from app.core.database import session_scope
from app.core.logging import get_logger
from app.schemas.brewery import BreweryCreate
from app.services.brewery import BreweryService

logger = get_logger(__name__)

# A curated seed set of real New Hampshire breweries. Coordinates are approximate
# taproom locations; websites are used by the discovery engine as the crawl root.
NH_BREWERIES: tuple[dict[str, object], ...] = (
    {
        "name": "Smuttynose Brewing Company",
        "website": "https://smuttynose.com",
        "city": "Hampton",
        "state": "NH",
        "latitude": 42.9376,
        "longitude": -70.8453,
    },
    {
        "name": "Stoneface Brewing Company",
        "website": "https://stonefacebrewing.com",
        "city": "Newington",
        "state": "NH",
        "latitude": 43.1006,
        "longitude": -70.8314,
    },
    {
        "name": "Great Rhythm Brewing Company",
        "website": "https://greatrhythmbrewing.com",
        "city": "Portsmouth",
        "state": "NH",
        "latitude": 43.0718,
        "longitude": -70.7626,
    },
    {
        "name": "Throwback Brewery",
        "website": "https://throwbackbrewery.com",
        "city": "North Hampton",
        "state": "NH",
        "latitude": 42.9723,
        "longitude": -70.8206,
    },
    {
        "name": "Henniker Brewing Company",
        "website": "https://hennikerbrewing.com",
        "city": "Henniker",
        "state": "NH",
        "latitude": 43.1787,
        "longitude": -71.8215,
    },
    {
        "name": "Schilling Beer Co.",
        "website": "https://schillingbeer.com",
        "city": "Littleton",
        "state": "NH",
        "latitude": 44.3060,
        "longitude": -71.7712,
    },
    {
        "name": "Tributary Brewing Company",
        "website": "https://tributarybrewingco.com",
        "city": "Kittery",
        "state": "NH",
        "latitude": 43.0895,
        "longitude": -70.7420,
    },
    {
        "name": "603 Brewery",
        "website": "https://603brewery.com",
        "city": "Londonderry",
        "state": "NH",
        "latitude": 42.8647,
        "longitude": -71.3745,
    },
)


async def import_nh_breweries() -> int:
    """Upsert the NH seed breweries. Returns the number processed."""

    async with session_scope() as session:
        service = BreweryService(session)
        for record in NH_BREWERIES:
            brewery = await service.upsert_by_slug(BreweryCreate(**record))  # type: ignore[arg-type]
            logger.info("Seeded brewery", extra={"slug": brewery.slug})
    return len(NH_BREWERIES)


def main() -> None:
    count = asyncio.run(import_nh_breweries())
    logger.info("NH brewery import complete", extra={"count": count})


if __name__ == "__main__":
    main()
