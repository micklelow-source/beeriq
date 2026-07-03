"""Demo activity seed for local preview/development.

Generates *authentic* data by driving the real services: it discovers a tap page
for one seeded brewery, records two extractions (producing real change events via
the diff engine), and computes two scores (producing an upward trend). Run after
``nh_breweries``::

    python -m app.seeds.demo_activity

Idempotent: it no-ops if the target brewery already has discovered URLs.
"""

from __future__ import annotations

import asyncio

from app.core.database import session_scope
from app.core.logging import get_logger
from app.models.discovered_url import DiscoveredURL, PageType
from app.repositories.brewery import BreweryRepository
from app.repositories.discovered_url import DiscoveredURLRepository
from app.schemas.extraction import (
    BeerExtraction,
    EventExtraction,
    FoodTruckExtraction,
    TapListExtraction,
)
from app.services.diff import DiffService
from app.services.scoring import ScoringService

logger = get_logger(__name__)

_TARGET_SLUG = "stoneface-brewing-company"


async def seed_demo_activity() -> bool:
    """Populate demo activity for one brewery. Returns True if it seeded."""

    async with session_scope() as session:
        brewery = await BreweryRepository(session).get_by_slug(_TARGET_SLUG)
        if brewery is None:
            logger.warning("Demo target not found; run nh_breweries first")
            return False

        urls = DiscoveredURLRepository(session)
        if await urls.list_for_brewery(brewery.id):
            logger.info("Demo activity already present; skipping")
            return False

        base = (brewery.website or "https://example.com").rstrip("/")
        tap = await urls.add(
            DiscoveredURL(
                brewery_id=brewery.id,
                url=f"{base}/on-tap",
                page_type=PageType.TAP,
                confidence=0.9,
            )
        )
        await urls.add(
            DiscoveredURL(
                brewery_id=brewery.id,
                url=f"{base}/events",
                page_type=PageType.EVENTS,
                confidence=0.8,
            )
        )

        diff = DiffService(session)
        scoring = ScoringService(session)

        baseline = TapListExtraction(
            beers=[
                BeerExtraction(name="Stoneface IPA", style="IPA", abv=7.2, availability="on tap"),
                BeerExtraction(name="Rye Pale Ale", style="Pale Ale", abv=5.6),
            ],
            hours="Wed–Sun 12–8",
            amenities=["dog friendly", "outdoor seating"],
        )
        await diff.record(tap, baseline)
        await session.flush()
        await scoring.compute_and_store(brewery.id)

        # Space the second extraction apart so "latest" is unambiguous on SQLite
        # (CURRENT_TIMESTAMP has second resolution).
        await asyncio.sleep(1.1)

        updated = TapListExtraction(
            beers=[
                BeerExtraction(name="Stoneface IPA", style="IPA", abv=7.4, availability="on tap"),
                BeerExtraction(name="Hazy Wonder", style="Hazy IPA", abv=6.5),
                BeerExtraction(name="Coffee Stout", style="Stout", abv=6.0, seasonal=True),
            ],
            events=[EventExtraction(title="Firkin Friday", date="Fridays 5pm")],
            food_trucks=[FoodTruckExtraction(name="Smokeshow BBQ", schedule="Saturdays")],
            hours="Wed–Sun 12–9",
            amenities=["dog friendly", "outdoor seating", "food"],
        )
        await diff.record(tap, updated)
        await session.flush()
        await scoring.compute_and_store(brewery.id)

    logger.info("Demo activity seeded for %s", _TARGET_SLUG)
    return True


def main() -> None:
    seeded = asyncio.run(seed_demo_activity())
    logger.info("Demo activity seed complete", extra={"seeded": seeded})


if __name__ == "__main__":
    main()
