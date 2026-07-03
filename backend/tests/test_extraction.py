"""Tests for the AI extraction layer (spec §3)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ai_provider
from app.core.config import Settings
from app.core.utils import html_to_text
from app.integrations.ai import FakeAIProvider, build_ai_provider
from app.integrations.ai.base import AIProvider
from app.main import create_app
from app.models.brewery import Brewery
from app.models.discovered_url import DiscoveredURL, PageType
from app.models.page_snapshot import PageSnapshot
from app.schemas.extraction import BeerExtraction, TapListExtraction
from app.services.extraction import ExtractionService


def test_html_to_text_strips_markup_and_scripts() -> None:
    html = (
        "<html><head><style>.x{color:red}</style></head>"
        "<body><h1>On Tap</h1><script>evil()</script><p>Hazy IPA 6.5%</p></body></html>"
    )
    text = html_to_text(html)
    assert "On Tap" in text
    assert "Hazy IPA 6.5%" in text
    assert "evil" not in text
    assert "color:red" not in text


def test_html_to_text_truncates() -> None:
    assert len(html_to_text("<p>" + "a" * 50_000 + "</p>", max_chars=100)) == 100


@pytest.mark.asyncio
async def test_extraction_service_returns_preset() -> None:
    preset = TapListExtraction(beers=[BeerExtraction(name="Hazy IPA", abv=6.5)])
    provider = FakeAIProvider(preset)

    result = await ExtractionService(provider).extract_from_html("<p>Hazy IPA</p>")

    assert result.beers[0].name == "Hazy IPA"
    # The page text (not raw HTML) is what the provider was prompted with.
    assert "Hazy IPA" in provider.prompts[0]
    assert "<p>" not in provider.prompts[0]


@pytest.mark.asyncio
async def test_extraction_service_empty_page_skips_provider() -> None:
    provider = FakeAIProvider()
    result = await ExtractionService(provider).extract_from_html("<html></html>")
    assert result == TapListExtraction()
    assert provider.prompts == []  # no call made for empty text


def test_factory_defaults_to_fake() -> None:
    provider = build_ai_provider(Settings(ai_provider="fake"))
    assert isinstance(provider, FakeAIProvider)
    assert isinstance(provider, AIProvider)


def test_factory_rejects_unimplemented_providers() -> None:
    with pytest.raises(NotImplementedError, match="openai"):
        build_ai_provider(Settings(ai_provider="openai"))


@pytest.mark.asyncio
async def test_extract_endpoint(session: AsyncSession) -> None:
    brewery = Brewery(name="Extract Co", slug="extract-co", website="https://e.com")
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id, url="https://e.com/tap", page_type=PageType.TAP, confidence=0.8
    )
    session.add(url)
    await session.flush()
    session.add(
        PageSnapshot(
            discovered_url_id=url.id,
            status_code=200,
            content_hash="a" * 64,
            html="<p>Hazy IPA 6.5% ABV</p>",
        )
    )
    await session.commit()

    preset = TapListExtraction(beers=[BeerExtraction(name="Hazy IPA", abv=6.5, style="IPA")])
    app = create_app()
    app.dependency_overrides[get_ai_provider] = lambda: FakeAIProvider(preset)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/breweries/{brewery.id}/urls/{url.id}/extract"
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["extraction"]["beers"][0]["name"] == "Hazy IPA"
    # First extraction for the URL is a baseline: no change events yet.
    assert body["changes"] == []


@pytest.mark.asyncio
async def test_extract_endpoint_requires_snapshot(session: AsyncSession) -> None:
    brewery = Brewery(name="No Snap", slug="no-snap", website="https://n.com")
    session.add(brewery)
    await session.flush()
    url = DiscoveredURL(
        brewery_id=brewery.id, url="https://n.com/tap", page_type=PageType.TAP, confidence=0.8
    )
    session.add(url)
    await session.commit()

    app = create_app()
    app.dependency_overrides[get_ai_provider] = lambda: FakeAIProvider()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/breweries/{brewery.id}/urls/{url.id}/extract"
        )
    assert resp.status_code == 409
