"""Tests for the diff engine (spec §4)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ai_provider
from app.integrations.ai import FakeAIProvider
from app.main import create_app
from app.models.brewery import Brewery
from app.models.change_event import ChangeEventType
from app.models.discovered_url import DiscoveredURL, PageType
from app.models.page_snapshot import PageSnapshot
from app.schemas.extraction import (
    BeerExtraction,
    EventExtraction,
    FoodTruckExtraction,
    TapListExtraction,
)
from app.services.diff import DiffService, diff_extractions


def _types(drafts) -> set[ChangeEventType]:
    return {d.event_type for d in drafts}


def test_diff_detects_added_and_removed_beers() -> None:
    previous = TapListExtraction(beers=[BeerExtraction(name="Stout")])
    latest = TapListExtraction(beers=[BeerExtraction(name="Hazy IPA")])
    drafts = diff_extractions(previous, latest)
    assert _types(drafts) == {ChangeEventType.BEER_ADDED, ChangeEventType.BEER_REMOVED}


def test_diff_detects_abv_and_description_changes() -> None:
    previous = TapListExtraction(beers=[BeerExtraction(name="IPA", abv=6.0, description="old")])
    latest = TapListExtraction(beers=[BeerExtraction(name="ipa", abv=6.5, description="new")])
    drafts = diff_extractions(previous, latest)
    assert _types(drafts) == {
        ChangeEventType.BEER_ABV_CHANGED,
        ChangeEventType.BEER_DESCRIPTION_CHANGED,
    }
    abv = next(d for d in drafts if d.event_type is ChangeEventType.BEER_ABV_CHANGED)
    assert abv.details == {"name": "ipa", "old_abv": 6.0, "new_abv": 6.5}


def test_diff_detects_events_trucks_and_hours() -> None:
    previous = TapListExtraction(hours="Mon-Fri 4-9")
    latest = TapListExtraction(
        events=[EventExtraction(title="Trivia Night")],
        food_trucks=[FoodTruckExtraction(name="Taco Truck")],
        hours="Mon-Sun 12-10",
    )
    drafts = diff_extractions(previous, latest)
    assert _types(drafts) == {
        ChangeEventType.EVENT_ADDED,
        ChangeEventType.FOOD_TRUCK_ADDED,
        ChangeEventType.HOURS_CHANGED,
    }


def test_diff_identical_extractions_yields_nothing() -> None:
    same = TapListExtraction(beers=[BeerExtraction(name="IPA", abv=6.0)])
    assert diff_extractions(same, same) == []


def test_diff_output_is_sorted_deterministically() -> None:
    previous = TapListExtraction(beers=[BeerExtraction(name="A")])
    latest = TapListExtraction(beers=[BeerExtraction(name="B"), BeerExtraction(name="C")])
    drafts = diff_extractions(previous, latest)
    keys = [(d.event_type.value, d.summary) for d in drafts]
    assert keys == sorted(keys)


async def _make_url(session: AsyncSession) -> DiscoveredURL:
    brewery = Brewery(name="Diff Co", slug="diff-co", website="https://d.com")
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id, url="https://d.com/tap", page_type=PageType.TAP, confidence=0.8
    )
    session.add(url)
    await session.commit()
    return url


@pytest.mark.asyncio
async def test_diff_service_baseline_then_change(session: AsyncSession) -> None:
    url = await _make_url(session)
    service = DiffService(session)

    baseline = await service.record(url, TapListExtraction(beers=[BeerExtraction(name="Stout")]))
    await session.commit()
    assert baseline == []  # first extraction is a baseline

    changes = await service.record(
        url, TapListExtraction(beers=[BeerExtraction(name="Hazy IPA")])
    )
    assert {c.event_type for c in changes} == {
        ChangeEventType.BEER_ADDED,
        ChangeEventType.BEER_REMOVED,
    }
    assert all(c.brewery_id == url.brewery_id for c in changes)


@pytest.mark.asyncio
async def test_changes_endpoint_lists_history(session: AsyncSession) -> None:
    brewery = Brewery(name="Hist Co", slug="hist-co", website="https://h.com")
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id, url="https://h.com/tap", page_type=PageType.TAP, confidence=0.8
    )
    session.add(url)
    await session.flush()
    session.add(
        PageSnapshot(
            discovered_url_id=url.id,
            status_code=200,
            content_hash="b" * 64,
            html="<p>Stout</p>",
        )
    )
    await session.commit()

    app = create_app()
    # First extract → Stout (baseline); second extract → Hazy IPA (produces changes).
    app.dependency_overrides[get_ai_provider] = lambda: FakeAIProvider(
        TapListExtraction(beers=[BeerExtraction(name="Stout")])
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(f"/api/v1/breweries/{brewery.id}/urls/{url.id}/extract")
        assert r1.json()["changes"] == []

        app.dependency_overrides[get_ai_provider] = lambda: FakeAIProvider(
            TapListExtraction(beers=[BeerExtraction(name="Hazy IPA")])
        )
        r2 = await client.post(f"/api/v1/breweries/{brewery.id}/urls/{url.id}/extract")
        assert len(r2.json()["changes"]) == 2

        listed = await client.get(f"/api/v1/breweries/{brewery.id}/changes")
    assert listed.status_code == 200
    page = listed.json()
    assert page["total"] == 2
    assert {c["event_type"] for c in page["items"]} == {"beer_added", "beer_removed"}
