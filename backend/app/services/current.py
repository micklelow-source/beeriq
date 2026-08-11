"""Current-data aggregation (spec §8).

Aggregates the *latest* stored extraction across a brewery's discovered URLs into
a single current view (tap list, events, food trucks, hours, amenities), and rolls
those up across all breweries for the events and food-truck directory pages.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brewery import Brewery
from app.models.discovered_url import DiscoveredURL
from app.models.extraction import Extraction
from app.repositories.brewery import BreweryRepository
from app.repositories.discovered_url import DiscoveredURLRepository
from app.repositories.extraction import ExtractionRepository
from app.schemas.extraction import (
    BeerExtraction,
    EventExtraction,
    FoodTruckExtraction,
    TapListExtraction,
)


def _dedup[T](items: list[T], key: Callable[[T], str]) -> list[T]:
    seen: dict[str, T] = {}
    for item in items:
        seen.setdefault(key(item).strip().lower(), item)
    return list(seen.values())


class CurrentDataService:
    """Produces the current, aggregated extraction view for breweries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.breweries = BreweryRepository(session)
        self.urls = DiscoveredURLRepository(session)
        self.extractions = ExtractionRepository(session)

    async def for_brewery(self, brewery_id: uuid.UUID) -> TapListExtraction:
        """Aggregate the latest extraction from each of a brewery's URLs."""

        beers: list[BeerExtraction] = []
        events: list[EventExtraction] = []
        trucks: list[FoodTruckExtraction] = []
        hours: str | None = None
        amenities: list[str] = []

        for url in await self.urls.list_for_brewery(brewery_id):
            extraction = await self.extractions.latest_for_url(url.id)
            if extraction is None:
                continue
            data = TapListExtraction.model_validate(extraction.payload)
            beers.extend(data.beers)
            events.extend(data.events)
            trucks.extend(data.food_trucks)
            if hours is None and data.hours:
                hours = data.hours
            amenities.extend(data.amenities)

        return TapListExtraction(
            beers=_dedup(beers, lambda b: b.name),
            events=_dedup(events, lambda e: e.title),
            food_trucks=_dedup(trucks, lambda f: f.name),
            hours=hours,
            amenities=sorted(set(amenities)),
        )

    async def _all_current(self) -> list[tuple[Brewery, TapListExtraction]]:
        """Return current data for every brewery that has any.

        A single query (using a window function to pick each discovered
        URL's latest extraction) rather than iterating every brewery in the
        directory one at a time -- that previous approach made two
        sequential DB round-trips per brewery, which was always an N+1 but
        only became a multi-minute hang once the directory grew past a few
        thousand breweries.
        """

        latest_rank = (
            func.row_number()
            .over(partition_by=Extraction.discovered_url_id, order_by=Extraction.created_at.desc())
            .label("rn")
        )
        ranked = select(
            Extraction.discovered_url_id,
            Extraction.payload,
            latest_rank,
        ).subquery()

        stmt = (
            select(Brewery, ranked.c.payload)
            .join(DiscoveredURL, DiscoveredURL.brewery_id == Brewery.id)
            .join(ranked, ranked.c.discovered_url_id == DiscoveredURL.id)
            .where(ranked.c.rn == 1)
        )
        rows = (await self.session.execute(stmt)).all()

        by_brewery: dict[uuid.UUID, tuple[Brewery, list[TapListExtraction]]] = {}
        for brewery, payload in rows:
            entry = by_brewery.setdefault(brewery.id, (brewery, []))
            entry[1].append(TapListExtraction.model_validate(payload))

        out: list[tuple[Brewery, TapListExtraction]] = []
        for brewery, extractions in by_brewery.values():
            current = TapListExtraction(
                beers=_dedup([b for e in extractions for b in e.beers], lambda b: b.name),
                events=_dedup([ev for e in extractions for ev in e.events], lambda ev: ev.title),
                food_trucks=_dedup(
                    [t for e in extractions for t in e.food_trucks], lambda t: t.name
                ),
                hours=next((e.hours for e in extractions if e.hours), None),
                amenities=sorted({a for e in extractions for a in e.amenities}),
            )
            if current.beers or current.events or current.food_trucks:
                out.append((brewery, current))
        return out

    async def all_events(self) -> list[tuple[Brewery, EventExtraction]]:
        return [
            (brewery, event)
            for brewery, current in await self._all_current()
            for event in current.events
        ]

    async def all_food_trucks(self) -> list[tuple[Brewery, FoodTruckExtraction]]:
        return [
            (brewery, truck)
            for brewery, current in await self._all_current()
            for truck in current.food_trucks
        ]
