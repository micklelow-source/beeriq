"""Brewery REST endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.repositories.brewery import BreweryRepository
from app.repositories.extraction import ExtractionRepository
from app.schemas.brewery import BreweryCreate, BreweryPage, BreweryRead
from app.schemas.extraction import TapListExtraction
from app.schemas.stats import BreweryStateStat
from app.services.brewery import BreweryService
from app.services.current import CurrentDataService

router = APIRouter(prefix="/breweries", tags=["breweries"])


def _to_read(brewery, tap_updated_at) -> BreweryRead:  # type: ignore[no-untyped-def]
    read = BreweryRead.model_validate(brewery)
    read.tap_updated_at = tap_updated_at
    return read


@router.post(
    "",
    response_model=BreweryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a brewery",
)
async def create_brewery(
    payload: BreweryCreate, session: AsyncSession = SessionDep
) -> BreweryRead:
    brewery = await BreweryService(session).create(payload)
    return BreweryRead.model_validate(brewery)


@router.get("", response_model=BreweryPage, summary="List breweries")
async def list_breweries(
    session: AsyncSession = SessionDep,
    state: str | None = Query(default=None, min_length=2, max_length=2),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> BreweryPage:
    items, total = await BreweryService(session).list(
        state=state, limit=limit, offset=offset
    )
    tap_times = await ExtractionRepository(session).latest_times_for_breweries(
        [b.id for b in items]
    )
    return BreweryPage(
        items=[_to_read(b, tap_times.get(b.id)) for b in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats/by-state",
    response_model=list[BreweryStateStat],
    summary="Brewery counts per state (for the map)",
)
async def stats_by_state(
    session: AsyncSession = SessionDep,
) -> list[BreweryStateStat]:
    repo = BreweryRepository(session)
    counts = await repo.count_by_state()
    with_taps = dict(await repo.count_with_taps_by_state())
    return [
        BreweryStateStat(state=state, count=count, with_taps=with_taps.get(state, 0))
        for state, count in counts
    ]


@router.get("/{brewery_id}", response_model=BreweryRead, summary="Get a brewery")
async def get_brewery(
    brewery_id: uuid.UUID, session: AsyncSession = SessionDep
) -> BreweryRead:
    brewery = await BreweryService(session).get(brewery_id)
    tap_times = await ExtractionRepository(session).latest_times_for_breweries([brewery.id])
    return _to_read(brewery, tap_times.get(brewery.id))


@router.get(
    "/{brewery_id}/current",
    response_model=TapListExtraction,
    summary="Current tap list, events, food trucks, and hours",
)
async def get_brewery_current(
    brewery_id: uuid.UUID, session: AsyncSession = SessionDep
) -> TapListExtraction:
    await BreweryService(session).get(brewery_id)  # 404 if unknown
    return await CurrentDataService(session).for_brewery(brewery_id)
