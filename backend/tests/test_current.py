"""Tests for current-data aggregation and directory endpoints (spec §8)."""

from __future__ import annotations

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

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/breweries/stats/by-state")
    assert resp.status_code == 200
    counts = {row["state"]: row["count"] for row in resp.json()}
    assert counts == {"NH": 2, "ME": 1}


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
async def test_current_endpoint_404_for_unknown(session: AsyncSession) -> None:  # noqa: ARG001
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/breweries/00000000-0000-0000-0000-000000000000/current"
        )
    assert resp.status_code == 404