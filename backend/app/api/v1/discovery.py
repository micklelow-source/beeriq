"""Discovery and scrape endpoints (spec §1–2)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AIProviderDep, FetcherDep, SessionDep
from app.integrations.ai import AIExtractionError, AIProvider
from app.integrations.fetcher import Fetcher
from app.repositories.discovered_url import DiscoveredURLRepository
from app.repositories.page_snapshot import PageSnapshotRepository
from app.schemas.discovery import (
    DiscoveredURLRead,
    DiscoveryResult,
    PageSnapshotRead,
    ScrapeResult,
)
from app.schemas.extraction import TapListExtraction
from app.services.brewery import BreweryService
from app.services.discovery import DiscoveryService
from app.services.extraction import ExtractionService
from app.services.scrape import ScrapeService

router = APIRouter(prefix="/breweries/{brewery_id}", tags=["discovery"])


@router.post(
    "/discover",
    response_model=DiscoveryResult,
    summary="Discover a brewery's tap/beer/menu/events pages",
)
async def discover_brewery(
    brewery_id: uuid.UUID,
    session: AsyncSession = SessionDep,
    fetcher: Fetcher = FetcherDep,
) -> DiscoveryResult:
    brewery = await BreweryService(session).get(brewery_id)
    try:
        discovered = await DiscoveryService(session, fetcher).discover(brewery)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return DiscoveryResult(
        brewery_id=brewery.id,
        discovered=[DiscoveredURLRead.model_validate(d) for d in discovered],
        probed=len(discovered),
    )


@router.get(
    "/urls",
    response_model=list[DiscoveredURLRead],
    summary="List discovered URLs for a brewery",
)
async def list_discovered_urls(
    brewery_id: uuid.UUID, session: AsyncSession = SessionDep
) -> list[DiscoveredURLRead]:
    # Ensure the brewery exists so unknown ids return 404, not an empty list.
    await BreweryService(session).get(brewery_id)
    urls = await DiscoveredURLRepository(session).list_for_brewery(brewery_id)
    return [DiscoveredURLRead.model_validate(u) for u in urls]


@router.post(
    "/urls/{url_id}/scrape",
    response_model=ScrapeResult,
    summary="Scrape a discovered URL and store a snapshot",
)
async def scrape_discovered_url(
    brewery_id: uuid.UUID,
    url_id: uuid.UUID,
    session: AsyncSession = SessionDep,
    fetcher: Fetcher = FetcherDep,
) -> ScrapeResult:
    repo = DiscoveredURLRepository(session)
    discovered = await repo.get(url_id)
    if discovered is None or discovered.brewery_id != brewery_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discovered URL not found")

    snapshot, changed = await ScrapeService(session, fetcher).scrape(discovered)
    return ScrapeResult(
        snapshot=PageSnapshotRead.model_validate(snapshot), changed=changed
    )


@router.post(
    "/urls/{url_id}/extract",
    response_model=TapListExtraction,
    summary="Extract structured data from a discovered URL's latest snapshot",
)
async def extract_discovered_url(
    brewery_id: uuid.UUID,
    url_id: uuid.UUID,
    session: AsyncSession = SessionDep,
    provider: AIProvider = AIProviderDep,
) -> TapListExtraction:
    repo = DiscoveredURLRepository(session)
    discovered = await repo.get(url_id)
    if discovered is None or discovered.brewery_id != brewery_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Discovered URL not found")

    snapshot = await PageSnapshotRepository(session).latest_for_url(url_id)
    if snapshot is None or snapshot.html is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No stored snapshot to extract from; scrape the URL first.",
        )

    try:
        return await ExtractionService(provider).extract_from_html(snapshot.html)
    except AIExtractionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
