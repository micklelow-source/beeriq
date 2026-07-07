"""Representative demo activity for local preview/development.

⚠️  The tap lists, events, and food trucks below are **representative sample data**,
not live values. Open Brewery DB provides only the brewery *directory*; real tap
lists/events/food trucks come from the scrape + AI-extraction pipeline (spec §1–3),
which needs an Anthropic API key (set ``BREWIQ_AI_PROVIDER=anthropic`` + key). This
seed drives the *real* diff and scoring services so the preview UI is populated with
authentic-shaped data.

    python -m app.seeds.demo_activity

Idempotent per brewery (skips any brewery that already has discovered URLs).
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


def _beers(*rows: tuple[str, str, float]) -> list[BeerExtraction]:
    return [BeerExtraction(name=n, style=s, abv=a, availability="on tap") for n, s, a in rows]


# slug -> full "current" tap page (representative sample).
_DEMO: dict[str, dict[str, object]] = {
    "603-brewery": {
        "beers": _beers(
            ("603 IPA", "IPA", 6.8),
            ("9th State", "Hazy IPA", 7.0),
            ("Winni Amber", "Amber Ale", 5.2),
            ("Blueberry Wheat", "Fruit Wheat", 4.9),
        ),
        "events": [EventExtraction(title="Live Music Saturdays", date="Saturdays 6pm")],
        "food_trucks": [FoodTruckExtraction(name="The Roaming Plow", schedule="Fri–Sat")],
        "hours": "Wed–Sun 12–8",
        "amenities": ["dog friendly", "outdoor seating", "food"],
    },
    "great-rhythm-brewing-company": {
        "beers": _beers(
            ("Resonation", "Pale Ale", 5.5),
            ("Squeeze", "Juicy IPA", 6.4),
            ("Émigré", "Coffee Stout", 6.0),
        ),
        "events": [EventExtraction(title="Trivia Night", date="Thursdays 7pm")],
        "food_trucks": [],
        "hours": "Mon–Sun 11–9",
        "amenities": ["dog friendly", "food"],
    },
    "henniker-brewing-company": {
        "beers": _beers(
            ("Working Man's Porter", "Porter", 5.9),
            ("Kölsch", "Kölsch", 4.8),
            ("Hopslinger", "IPA", 6.4),
        ),
        "events": [],
        "food_trucks": [FoodTruckExtraction(name="Smoke & Barrel BBQ", schedule="Saturdays")],
        "hours": "Wed–Sun 12–7",
        "amenities": ["outdoor seating"],
    },
    "schilling-beer-co": {
        "beers": _beers(
            ("Alexandr", "Czech Pilsner", 4.9),
            ("Modernism", "Hazy IPA", 6.5),
            ("Landbier", "Kellerbier", 5.0),
            ("Palmovka", "Dark Lager", 4.4),
        ),
        "events": [EventExtraction(title="Firkin Friday", date="Fridays 4pm")],
        "food_trucks": [],
        "hours": "Sun–Thu 11:30–9, Fri–Sat 11:30–10",
        "amenities": ["outdoor seating", "food", "riverside"],
    },
    "smuttynose-brewing-company": {
        "beers": _beers(
            ("Finestkind", "IPA", 6.9),
            ("Old Brown Dog", "Brown Ale", 5.6),
            ("Shoals", "Pale Ale", 5.4),
        ),
        "events": [EventExtraction(title="Live Music Weekends", date="Fri–Sat")],
        "food_trucks": [FoodTruckExtraction(name="Hayseed Restaurant", schedule="On site")],
        "hours": "Mon–Sun 11:30–9",
        "amenities": ["dog friendly", "food", "restaurant"],
    },
    "throwback-brewery": {
        "beers": _beers(
            ("Hog Happy Hefe", "Hefeweizen", 5.0),
            ("Maple Kissed Wheat Porter", "Porter", 5.8),
            ("Dippity Do", "Hazy IPA", 6.6),
        ),
        "events": [EventExtraction(title="Farm-to-Table Dinner", date="Last Friday monthly")],
        "food_trucks": [],
        "hours": "Wed–Sun 12–8",
        "amenities": ["dog friendly", "outdoor seating", "farm", "food"],
    },
}


async def seed_demo_activity() -> int:
    """Populate representative activity for several breweries. Returns count seeded."""

    seeded = 0
    async with session_scope() as session:
        breweries = BreweryRepository(session)
        urls = DiscoveredURLRepository(session)
        diff = DiffService(session)
        scoring = ScoringService(session)

        for slug, data in _DEMO.items():
            brewery = await breweries.get_by_slug(slug)
            if brewery is None:
                continue
            if await urls.list_for_brewery(brewery.id):
                continue  # already seeded

            base = (brewery.website or "https://example.com").rstrip("/")
            tap = await urls.add(
                DiscoveredURL(
                    brewery_id=brewery.id,
                    url=f"{base}/on-tap",
                    page_type=PageType.TAP,
                    confidence=0.9,
                )
            )
            if data["events"]:
                await urls.add(
                    DiscoveredURL(
                        brewery_id=brewery.id,
                        url=f"{base}/events",
                        page_type=PageType.EVENTS,
                        confidence=0.8,
                    )
                )

            extraction = TapListExtraction(
                beers=data["beers"],  # type: ignore[arg-type]
                events=data["events"],  # type: ignore[arg-type]
                food_trucks=data["food_trucks"],  # type: ignore[arg-type]
                hours=data["hours"],  # type: ignore[arg-type]
                amenities=data["amenities"],  # type: ignore[arg-type]
            )
            await diff.record(tap, extraction)
            await session.flush()
            await scoring.compute_and_store(brewery.id)
            seeded += 1

    logger.info("Demo activity seeded", extra={"breweries": seeded})
    return seeded


def main() -> None:
    count = asyncio.run(seed_demo_activity())
    logger.info("Demo activity seed complete", extra={"seeded": count})


if __name__ == "__main__":
    main()
