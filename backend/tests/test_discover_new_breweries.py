"""Tests for the discover_new_breweries orchestration (directory refresh ->
scrape only what's new). The two pieces it glues together (Open Brewery DB
fetching and the scrape pipeline) are network-bound and out of scope here;
this only verifies the orchestration logic itself."""

from __future__ import annotations

import uuid

import pytest

from app.seeds import discover_new_breweries as module


@pytest.mark.asyncio
async def test_discover_new_breweries_scrapes_only_new_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    new_id_nh = uuid.uuid4()
    new_id_me = uuid.uuid4()

    async def fake_import_state_directory(state_code: str):
        if state_code == "NH":
            return 10, [new_id_nh]
        if state_code == "ME":
            return 5, [new_id_me]
        return 3, []  # VT: nothing new

    scraped_with: list[uuid.UUID] = []

    async def fake_scrape_specific_breweries(brewery_ids, *, concurrency=15):
        scraped_with.extend(brewery_ids)
        return {"attempted": len(brewery_ids), "with_taps": 1, "beers": 4, "errors": 0}

    monkeypatch.setattr(module, "import_state_directory", fake_import_state_directory)
    monkeypatch.setattr(module, "scrape_specific_breweries", fake_scrape_specific_breweries)

    stats = await module.discover_new_breweries(["NH", "ME", "VT"])

    assert sorted(scraped_with) == sorted([new_id_nh, new_id_me])
    assert stats["imported"] == 18
    assert stats["new_breweries"] == 2
    assert stats["with_taps"] == 1
    assert stats["beers"] == 4


@pytest.mark.asyncio
async def test_discover_new_breweries_skips_scrape_when_nothing_new(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_import_state_directory(state_code: str):
        return 7, []

    called_with = None

    async def fake_scrape_specific_breweries(brewery_ids, *, concurrency=15):
        nonlocal called_with
        called_with = list(brewery_ids)
        return {"attempted": 0, "with_taps": 0, "beers": 0, "errors": 0}

    monkeypatch.setattr(module, "import_state_directory", fake_import_state_directory)
    monkeypatch.setattr(module, "scrape_specific_breweries", fake_scrape_specific_breweries)

    stats = await module.discover_new_breweries(["NH"])

    assert called_with == []
    assert stats["new_breweries"] == 0
    assert stats["attempted"] == 0
