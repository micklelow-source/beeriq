"""Tests for the Website Discovery Engine."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brewery import Brewery
from app.models.discovered_url import PageType
from app.services.discovery import DiscoveryService
from tests.conftest import FakeFetcher


async def _make_brewery(session: AsyncSession) -> Brewery:
    brewery = Brewery(name="Test Brewery", slug="test-brewery", website="https://example.com")
    session.add(brewery)
    await session.commit()
    return brewery


@pytest.mark.asyncio
async def test_discovery_finds_probed_and_linked_pages(session: AsyncSession) -> None:
    brewery = await _make_brewery(session)

    fetcher = FakeFetcher()
    fetcher.set(
        "https://example.com/",
        '<html><body>'
        '<a href="/events">Events Calendar</a>'
        '<a href="https://facebook.com/test">Facebook</a>'
        "</body></html>",
    )
    fetcher.set("https://example.com/tap", "current taplist")
    fetcher.set("https://example.com/beers", "our beers")
    fetcher.set("https://example.com/events", "upcoming events")

    discovered = await DiscoveryService(session, fetcher).discover(brewery)
    by_url = {d.url: d for d in discovered}

    assert "https://example.com/tap" in by_url
    assert by_url["https://example.com/tap"].page_type is PageType.TAP
    assert by_url["https://example.com/beers"].page_type is PageType.BEER
    assert by_url["https://example.com/events"].page_type is PageType.EVENTS

    # Off-site links (Facebook) and unreachable candidates (404) are excluded.
    assert not any("facebook.com" in url for url in by_url)
    assert "https://example.com/menu" not in by_url


@pytest.mark.asyncio
async def test_discovery_is_idempotent(session: AsyncSession) -> None:
    brewery = await _make_brewery(session)
    fetcher = FakeFetcher({"https://example.com/tap": "taplist"})

    service = DiscoveryService(session, fetcher)
    first = await service.discover(brewery)
    await session.commit()
    second = await service.discover(brewery)

    assert len(first) == 1
    # Re-running does not create duplicate rows.
    assert {d.url for d in second} == {d.url for d in first}


@pytest.mark.asyncio
async def test_discovery_requires_website(session: AsyncSession) -> None:
    brewery = Brewery(name="No Site", slug="no-site", website=None)
    session.add(brewery)
    await session.commit()

    with pytest.raises(ValueError, match="no website"):
        await DiscoveryService(session, FakeFetcher()).discover(brewery)
