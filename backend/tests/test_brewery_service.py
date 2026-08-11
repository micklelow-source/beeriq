"""Tests for BreweryService.upsert_by_slug's backfill-only-empty-fields behavior."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.brewery import BreweryCreate
from app.services.brewery import BreweryService


@pytest.mark.asyncio
async def test_upsert_creates_new_brewery(session: AsyncSession) -> None:
    service = BreweryService(session)
    brewery, created = await service.upsert_by_slug(
        BreweryCreate(name="New Co", state="NH", website="https://newco.example.com")
    )
    assert created is True
    assert brewery.slug == "new-co"
    assert brewery.website == "https://newco.example.com/"


@pytest.mark.asyncio
async def test_upsert_backfills_missing_fields_on_existing_brewery(session: AsyncSession) -> None:
    service = BreweryService(session)
    original, created = await service.upsert_by_slug(BreweryCreate(name="Gap Co", state="NH"))
    assert created is True
    assert original.website is None
    assert original.city is None

    updated, created_again = await service.upsert_by_slug(
        BreweryCreate(
            name="Gap Co",
            state="NH",
            website="https://gapco.example.com",
            city="Manchester",
        )
    )
    assert created_again is False
    assert updated.id == original.id
    assert updated.website == "https://gapco.example.com/"
    assert updated.city == "Manchester"


@pytest.mark.asyncio
async def test_upsert_never_overwrites_existing_website(session: AsyncSession) -> None:
    """A manually-corrected website (e.g. fixing a hijacked domain) must
    survive a re-import that carries a different (stale) upstream value."""

    service = BreweryService(session)
    await service.upsert_by_slug(
        BreweryCreate(name="Fixed Co", state="NH", website="https://corrected-domain.example.com")
    )

    reimported, created = await service.upsert_by_slug(
        BreweryCreate(name="Fixed Co", state="NH", website="https://stale-hijacked-domain.example.com")
    )
    assert created is False
    assert reimported.website == "https://corrected-domain.example.com/"
