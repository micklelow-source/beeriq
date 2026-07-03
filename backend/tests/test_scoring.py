"""Tests for BrewIQ Score v2 (spec §5)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.models.brewery import Brewery
from app.models.discovered_url import DiscoveredURL, PageType
from app.models.extraction import Extraction
from app.schemas.extraction import BeerExtraction, EventExtraction, TapListExtraction
from app.services.scoring import ScoringInputs, ScoringService, compute_score

NOW = datetime(2026, 7, 3, tzinfo=UTC)


def _empty_inputs() -> ScoringInputs:
    return ScoringInputs(
        now=NOW,
        latest_extraction_at=None,
        extraction_count=0,
        beers=[],
        events=[],
        discovered_page_types=set(),
        has_events_page=False,
        rotation_changes_recent=0,
    )


def _rich_inputs() -> ScoringInputs:
    return ScoringInputs(
        now=NOW,
        latest_extraction_at=NOW - timedelta(days=1),
        extraction_count=12,
        beers=[
            BeerExtraction(name="A", style="IPA"),
            BeerExtraction(name="B", style="Stout"),
            BeerExtraction(name="C", style="Lager"),
            BeerExtraction(name="D", style="Pilsner"),
        ],
        events=[
            EventExtraction(title="Trivia"),
            EventExtraction(title="Live Music"),
            EventExtraction(title="Yoga"),
        ],
        discovered_page_types={
            PageType.TAP,
            PageType.BEER,
            PageType.MENU,
            PageType.EVENTS,
            PageType.FOOD_TRUCK,
        },
        has_events_page=True,
        rotation_changes_recent=4,
    )


def test_empty_inputs_score_is_zero_with_no_confidence() -> None:
    result = compute_score(_empty_inputs())
    assert result.overall == 0.0
    assert result.data_confidence == 0.0
    assert all(not c.available for c in result.components)
    assert result.trend_direction == "new"


def test_rich_inputs_score_is_high() -> None:
    result = compute_score(_rich_inputs(), previous_overall=50.0)
    assert result.overall > 70
    # Every component except social_activity has data.
    assert result.data_confidence == 0.95
    social = next(c for c in result.components if c.name == "social_activity")
    assert social.available is False
    assert result.trend_direction == "up"
    assert result.trend_delta is not None and result.trend_delta > 0


def test_trend_flat_and_down() -> None:
    inputs = _rich_inputs()
    overall = compute_score(inputs).overall
    assert compute_score(inputs, previous_overall=overall).trend_direction == "flat"
    assert compute_score(inputs, previous_overall=overall + 20).trend_direction == "down"


def test_recommendations_flag_missing_signals() -> None:
    result = compute_score(_empty_inputs())
    joined = " ".join(result.recommendations).lower()
    assert "tap page" in joined
    assert "social" in joined


async def _make_scored_brewery(session: AsyncSession) -> Brewery:
    brewery = Brewery(name="Score Co", slug="score-co", website="https://s.com")
    session.add(brewery)
    await session.flush()
    tap = DiscoveredURL(
        brewery_id=brewery.id, url="https://s.com/tap", page_type=PageType.TAP, confidence=0.8
    )
    session.add(tap)
    await session.flush()
    payload = TapListExtraction(
        beers=[BeerExtraction(name="Hazy IPA", style="IPA")]
    ).model_dump(mode="json")
    session.add(Extraction(discovered_url_id=tap.id, payload=payload))
    await session.commit()
    return brewery


@pytest.mark.asyncio
async def test_scoring_service_persists_and_trends(session: AsyncSession) -> None:
    brewery = await _make_scored_brewery(session)
    service = ScoringService(session)

    first = await service.compute_and_store(brewery.id)
    await session.commit()
    assert first.overall > 0
    assert first.trend_direction == "new"

    second = await service.compute_and_store(brewery.id)
    assert second.trend_direction == "flat"  # same data → no movement


@pytest.mark.asyncio
async def test_score_endpoints(session: AsyncSession) -> None:
    brewery = await _make_scored_brewery(session)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # No score computed yet.
        assert (await client.get(f"/api/v1/breweries/{brewery.id}/score")).status_code == 404

        post = await client.post(f"/api/v1/breweries/{brewery.id}/score")
        assert post.status_code == 200, post.text
        body = post.json()
        assert body["overall"] > 0
        assert body["trend"]["direction"] == "new"
        assert any(c["name"] == "freshness" for c in body["components"])

        get = await client.get(f"/api/v1/breweries/{brewery.id}/score")
        assert get.status_code == 200
        assert get.json()["overall"] == body["overall"]


@pytest.mark.asyncio
async def test_score_unknown_brewery_404(session: AsyncSession) -> None:  # noqa: ARG001
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/breweries/00000000-0000-0000-0000-000000000000/score"
        )
    assert resp.status_code == 404
