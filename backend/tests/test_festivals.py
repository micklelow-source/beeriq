"""Tests for the curated festivals/tastings endpoint."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.models.festival import Festival, FestivalCategory
from app.repositories.festival import FestivalRepository

TODAY = date(2026, 8, 13)


@pytest.mark.asyncio
async def test_list_upcoming_orders_by_date_and_pushes_undated_last(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            Festival(
                slug="past-2026", name="Past Fest", event_date=TODAY - timedelta(days=1), state="NH"
            ),
            Festival(
                slug="soonest-2026",
                name="Soonest Fest",
                event_date=TODAY + timedelta(days=1),
                state="NH",
            ),
            Festival(
                slug="later-2026",
                name="Later Fest",
                event_date=TODAY + timedelta(days=10),
                state="NH",
            ),
            Festival(slug="undated-2026", name="Undated Fest", event_date=None, state="NH"),
        ]
    )
    await session.commit()

    upcoming = await FestivalRepository(session).list_upcoming(on_or_after=TODAY)
    assert [f.name for f in upcoming] == ["Soonest Fest", "Later Fest", "Undated Fest"]


@pytest.mark.asyncio
async def test_festivals_endpoint_returns_category_and_source(session: AsyncSession) -> None:
    session.add(
        Festival(
            slug="tasting-2026",
            name="Uncorked Tasting",
            category=FestivalCategory.TASTING,
            event_date=TODAY + timedelta(days=5),
            city="East Hanover",
            state="NJ",
            url="https://beerfests.com/us/new-jersey-beer-festivals",
        )
    )
    await session.commit()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/festivals")

    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["name"] == "Uncorked Tasting"
    assert body[0]["category"] == "tasting"
    assert body[0]["source"] == "beerfests.com"
    assert body[0]["state"] == "NJ"


@pytest.mark.asyncio
async def test_seed_is_idempotent_by_slug(session: AsyncSession) -> None:
    from app.seeds.festivals import _ROWS, _slug_for

    repo = FestivalRepository(session)
    row = _ROWS[0]
    slug = _slug_for(row)
    assert await repo.get_by_slug(slug) is None

    festival = Festival(slug=slug, name=row.name, event_date=row.event_date, state=row.state)
    await repo.add(festival)
    await session.commit()

    again = await repo.get_by_slug(slug)
    assert again is not None
    assert again.id == festival.id
