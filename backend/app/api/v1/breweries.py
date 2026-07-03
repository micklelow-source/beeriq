"""Brewery REST endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.schemas.brewery import BreweryCreate, BreweryPage, BreweryRead
from app.services.brewery import BreweryService

router = APIRouter(prefix="/breweries", tags=["breweries"])


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
    return BreweryPage(
        items=[BreweryRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{brewery_id}", response_model=BreweryRead, summary="Get a brewery")
async def get_brewery(
    brewery_id: uuid.UUID, session: AsyncSession = SessionDep
) -> BreweryRead:
    brewery = await BreweryService(session).get(brewery_id)
    return BreweryRead.model_validate(brewery)
