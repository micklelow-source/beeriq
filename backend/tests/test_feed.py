"""Tests for the live activity feed (spec §8)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.models.brewery import Brewery
from app.models.brewery_score import BreweryScore
from app.models.change_event import ChangeEvent, ChangeEventType
from app.models.discovered_url import DiscoveredURL, PageType
from app.services.feed import FeedService


async def _brewery_with_url(session: AsyncSession, name: str) -> DiscoveredURL:
    brewery = Brewery(name=name, slug=name.lower().replace(" ", "-"), website="https://x.com")
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id, url=f"https://x.com/{name}", page_type=PageType.TAP, confidence=0.8
    )
    session.add(url)
    await session.flush()
    return url


async def _seed(session: AsyncSession) -> None:
    a = await _brewery_with_url(session, "Alpha")
    b = await _brewery_with_url(session, "Beta")
    session.add_all(
        [
            ChangeEvent(
                brewery_id=a.brewery_id,
                discovered_url_id=a.id,
                event_type=ChangeEventType.BEER_ADDED,
                summary="New beer: Hazy IPA",
                details={"name": "Hazy IPA"},
            ),
            ChangeEvent(
                brewery_id=a.brewery_id,
                discovered_url_id=a.id,
                event_type=ChangeEventType.EVENT_ADDED,
                summary="New event: Trivia",
                details={"title": "Trivia"},
            ),
            ChangeEvent(
                brewery_id=b.brewery_id,
                discovered_url_id=b.id,
                event_type=ChangeEventType.FOOD_TRUCK_ADDED,
                summary="Food truck announced: Tacos",
                details={"name": "Tacos"},
            ),
            BreweryScore(
                brewery_id=b.brewery_id,
                overall=82.0,
                data_confidence=0.9,
                components=[],
                recommendations=[],
                trend_direction="up",
                trend_delta=5.0,
            ),
        ]
    )
    await session.commit()


@pytest.mark.asyncio
async def test_empty_feed(session: AsyncSession) -> None:
    items, total = await FeedService(session).page(limit=25, offset=0)
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_feed_merges_changes_and_score_increases(session: AsyncSession) -> None:
    await _seed(session)
    items, total = await FeedService(session).page(limit=25, offset=0)

    assert total == 4
    kinds = {i.kind for i in items}
    assert kinds == {"change_event", "score_increase"}
    assert all(i.brewery_name for i in items)

    score_item = next(i for i in items if i.kind == "score_increase")
    assert "score rose to 82.0" in score_item.summary.lower()
    assert score_item.details == {"overall": 82.0, "delta": 5.0}

    # Change-event items expose their event_type so clients can badge them.
    change_types = {
        i.details.get("event_type") for i in items if i.kind == "change_event"
    }
    assert "food_truck_added" in change_types


@pytest.mark.asyncio
async def test_feed_pagination(session: AsyncSession) -> None:
    await _seed(session)
    page1, total = await FeedService(session).page(limit=2, offset=0)
    page2, _ = await FeedService(session).page(limit=2, offset=2)
    assert total == 4
    assert len(page1) == 2
    assert len(page2) == 2
    # No overlap between the two pages.
    assert {i.id for i in page1}.isdisjoint({i.id for i in page2})


@pytest.mark.asyncio
async def test_feed_endpoint(session: AsyncSession) -> None:
    await _seed(session)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/feed", params={"limit": 25})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    assert {i["kind"] for i in body["items"]} == {"change_event", "score_increase"}
