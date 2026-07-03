"""Integration tests for the brewery REST endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_brewery(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/breweries",
        json={
            "name": "Stoneface Brewing",
            "website": "https://stonefacebrewing.com",
            "state": "NH",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["slug"] == "stoneface-brewing"
    assert body["state"] == "NH"

    get_resp = await client.get(f"/api/v1/breweries/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Stoneface Brewing"


@pytest.mark.asyncio
async def test_duplicate_slug_conflicts(client: AsyncClient) -> None:
    payload = {"name": "Duplicate Co"}
    first = await client.post("/api/v1/breweries", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/breweries", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_list_breweries_pagination_and_state_filter(client: AsyncClient) -> None:
    await client.post("/api/v1/breweries", json={"name": "NH One", "state": "NH"})
    await client.post("/api/v1/breweries", json={"name": "ME One", "state": "ME"})

    resp = await client.get("/api/v1/breweries", params={"state": "NH"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(item["state"] == "NH" for item in data["items"])


@pytest.mark.asyncio
async def test_get_unknown_brewery_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/breweries/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
