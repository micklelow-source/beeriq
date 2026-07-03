"""Integration test for the discovery/scrape endpoints using a patched fetcher."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_fetcher
from app.main import create_app
from tests.conftest import FakeFetcher


@pytest.mark.asyncio
async def test_discover_endpoint_uses_injected_fetcher() -> None:
    fetcher = FakeFetcher(
        {
            "https://example.com/": '<a href="/events">Events</a>',
            "https://example.com/tap": "taplist",
            "https://example.com/events": "events",
        }
    )

    app = create_app()
    # Override the fetcher dependency so no real network calls are made.
    app.dependency_overrides[get_fetcher] = lambda: fetcher

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/v1/breweries",
            json={"name": "Example Brewery", "website": "https://example.com"},
        )
        brewery_id = created.json()["id"]

        discover = await client.post(f"/api/v1/breweries/{brewery_id}/discover")
        assert discover.status_code == 200, discover.text
        urls = {d["url"] for d in discover.json()["discovered"]}
        assert "https://example.com/tap" in urls
        assert "https://example.com/events" in urls

        listed = await client.get(f"/api/v1/breweries/{brewery_id}/urls")
        assert listed.status_code == 200
        assert len(listed.json()) == len(urls)
