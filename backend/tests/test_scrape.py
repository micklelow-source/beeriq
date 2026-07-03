"""Tests for the scrape/snapshot service and change detection."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.fetcher import FetchResponse
from app.models.brewery import Brewery
from app.models.discovered_url import DiscoveredURL, PageType
from app.services.scrape import ScrapeService
from tests.conftest import FakeFetcher


async def _make_discovered(session: AsyncSession) -> DiscoveredURL:
    brewery = Brewery(name="Scrape Co", slug="scrape-co", website="https://s.com")
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id,
        url="https://s.com/tap",
        page_type=PageType.TAP,
        confidence=0.8,
    )
    session.add(url)
    await session.commit()
    return url


@pytest.mark.asyncio
async def test_first_scrape_stores_snapshot_marked_changed(session: AsyncSession) -> None:
    url = await _make_discovered(session)
    fetcher = FakeFetcher({"https://s.com/tap": "Hazy IPA, Stout"})

    snapshot, changed = await ScrapeService(session, fetcher).scrape(url)

    assert changed is True
    assert snapshot.status_code == 200
    assert snapshot.html == "Hazy IPA, Stout"
    assert len(snapshot.content_hash) == 64


@pytest.mark.asyncio
async def test_identical_content_is_not_changed(session: AsyncSession) -> None:
    url = await _make_discovered(session)
    fetcher = FakeFetcher({"https://s.com/tap": "same body"})
    service = ScrapeService(session, fetcher)

    _, first_changed = await service.scrape(url)
    await session.commit()
    _, second_changed = await service.scrape(url)

    assert first_changed is True
    assert second_changed is False


@pytest.mark.asyncio
async def test_304_returns_previous_snapshot(session: AsyncSession) -> None:
    url = await _make_discovered(session)
    service = ScrapeService(session, FakeFetcher({"https://s.com/tap": "body v1"}))
    original, _ = await service.scrape(url)
    await session.commit()

    not_modified = FakeFetcher(
        {"https://s.com/tap": FetchResponse("https://s.com/tap", 304, "", {})}
    )
    snapshot, changed = await ScrapeService(session, not_modified).scrape(url)

    assert changed is False
    assert snapshot.id == original.id


@pytest.mark.asyncio
async def test_failed_fetch_without_history_raises(session: AsyncSession) -> None:
    url = await _make_discovered(session)
    fetcher = FakeFetcher()  # every URL 404s

    with pytest.raises(RuntimeError, match="Failed to fetch"):
        await ScrapeService(session, fetcher).scrape(url)
