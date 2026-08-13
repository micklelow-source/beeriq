"""Tests for current-data aggregation and directory endpoints (spec §8)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.models.brewery import Brewery
from app.models.discovered_url import DiscoveredURL, PageType
from app.models.extraction import Extraction
from app.schemas.extraction import (
    BeerExtraction,
    EventExtraction,
    FoodTruckExtraction,
    TapListExtraction,
)
from app.services.current import CurrentDataService


async def _brewery_with_extraction(
    session: AsyncSession, name: str, state: str, payload: TapListExtraction
) -> Brewery:
    brewery = Brewery(
        name=name, slug=name.lower().replace(" ", "-"), website="https://x.com", state=state
    )
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id, url=f"https://x.com/{name}", page_type=PageType.TAP, confidence=0.9
    )
    session.add(url)
    await session.flush()
    session.add(
        Extraction(discovered_url_id=url.id, payload=payload.model_dump(mode="json"))
    )
    await session.commit()
    return brewery


@pytest.mark.asyncio
async def test_current_aggregates_latest_extraction(session: AsyncSession) -> None:
    payload = TapListExtraction(
        beers=[BeerExtraction(name="Hazy IPA", style="IPA", abv=6.5)],
        events=[EventExtraction(title="Trivia")],
        food_trucks=[FoodTruckExtraction(name="Tacos")],
        hours="Wed-Sun 12-9",
        amenities=["dog friendly"],
    )
    brewery = await _brewery_with_extraction(session, "Cur Co", "NH", payload)

    current = await CurrentDataService(session).for_brewery(brewery.id)
    assert [b.name for b in current.beers] == ["Hazy IPA"]
    assert current.events[0].title == "Trivia"
    assert current.food_trucks[0].name == "Tacos"
    assert current.hours == "Wed-Sun 12-9"


@pytest.mark.asyncio
async def test_stats_by_state_endpoint(session: AsyncSession) -> None:
    await _brewery_with_extraction(session, "A", "NH", TapListExtraction())
    await _brewery_with_extraction(session, "B", "NH", TapListExtraction())
    await _brewery_with_extraction(session, "C", "ME", TapListExtraction())
    # No tap data at all: should count toward "count" but not "with_taps".
    session.add(Brewery(name="D", slug="d", website="https://d.com", state="VT"))
    await session.commit()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/breweries/stats/by-state")
    assert resp.status_code == 200
    rows = {row["state"]: row for row in resp.json()}
    assert rows["NH"]["count"] == 2 and rows["NH"]["with_taps"] == 2
    assert rows["ME"]["count"] == 1 and rows["ME"]["with_taps"] == 1
    assert rows["VT"]["count"] == 1 and rows["VT"]["with_taps"] == 0


@pytest.mark.asyncio
async def test_events_and_food_trucks_endpoints(session: AsyncSession) -> None:
    await _brewery_with_extraction(
        session,
        "Eventful",
        "NH",
        TapListExtraction(
            events=[EventExtraction(title="Yoga & Beer", date="Sundays")],
            food_trucks=[FoodTruckExtraction(name="BBQ Pit", schedule="Saturdays")],
        ),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        events = await client.get("/api/v1/events")
        trucks = await client.get("/api/v1/food-trucks")

    assert events.status_code == 200
    assert events.json()[0]["title"] == "Yoga & Beer"
    assert events.json()[0]["brewery_name"] == "Eventful"

    assert trucks.status_code == 200
    assert trucks.json()[0]["name"] == "BBQ Pit"
    assert trucks.json()[0]["brewery_state"] == "NH"


@pytest.mark.asyncio
async def test_all_events_merges_across_multiple_urls_and_uses_only_latest(
    session: AsyncSession,
) -> None:
    """The batched all_events()/all_food_trucks() query must reproduce what
    for_brewery() does for a single brewery: merge data from every
    discovered URL, dedup by title/name, and use only each URL's most
    recent extraction -- not a superseded one."""

    brewery = Brewery(name="Multi URL Co", slug="multi-url-co", website="https://m.com", state="NH")
    session.add(brewery)
    await session.flush()

    url_a = DiscoveredURL(
        brewery_id=brewery.id, url="https://m.com/events", page_type=PageType.EVENTS, confidence=0.9
    )
    url_b = DiscoveredURL(
        brewery_id=brewery.id,
        url="https://m.com/trucks",
        page_type=PageType.FOOD_TRUCK,
        confidence=0.9,
    )
    session.add_all([url_a, url_b])
    await session.flush()

    # url_a: a superseded extraction (no events) followed by the real one.
    # created_at is set explicitly (rather than relying on two inserts
    # landing in different seconds) since the "latest" query only orders by
    # created_at -- ties are otherwise possible when extractions are
    # recorded in quick succession, as they are here.
    now = datetime.now(UTC)
    session.add_all(
        [
            Extraction(
                discovered_url_id=url_a.id,
                payload=TapListExtraction().model_dump(mode="json"),
                created_at=now - timedelta(minutes=5),
            ),
            Extraction(
                discovered_url_id=url_a.id,
                payload=TapListExtraction(
                    events=[EventExtraction(title="Trivia Night")]
                ).model_dump(mode="json"),
                created_at=now,
            ),
            # url_b: its own event plus a food truck.
            Extraction(
                discovered_url_id=url_b.id,
                payload=TapListExtraction(
                    events=[EventExtraction(title="Live Music")],
                    food_trucks=[FoodTruckExtraction(name="Tacos El Rey")],
                ).model_dump(mode="json"),
                created_at=now,
            ),
        ]
    )
    await session.commit()

    service = CurrentDataService(session)
    events = await service.all_events()
    trucks = await service.all_food_trucks()

    event_titles = {e.title for _, e in events}
    assert event_titles == {"Trivia Night", "Live Music"}
    assert [t.name for _, t in trucks] == ["Tacos El Rey"]


@pytest.mark.asyncio
async def test_all_events_skips_breweries_with_no_extractions(session: AsyncSession) -> None:
    """A brewery with zero discovered URLs (or none with an extraction)
    must not appear in the aggregate at all."""

    session.add(Brewery(name="Empty Co", slug="empty-co", website="https://e.com", state="NH"))
    await session.commit()

    service = CurrentDataService(session)
    assert await service.all_events() == []
    assert await service.all_food_trucks() == []


@pytest.mark.asyncio
async def test_current_endpoint_404_for_unknown(session: AsyncSession) -> None:  # noqa: ARG001
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/breweries/00000000-0000-0000-0000-000000000000/current"
        )
    assert resp.status_code == 404