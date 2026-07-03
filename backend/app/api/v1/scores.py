"""BrewIQ score endpoints (spec §5)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.repositories.brewery_score import BreweryScoreRepository
from app.schemas.score import BrewIQScoreRead
from app.services.brewery import BreweryService
from app.services.scoring import ScoringService

router = APIRouter(prefix="/breweries/{brewery_id}", tags=["scores"])


@router.post(
    "/score",
    response_model=BrewIQScoreRead,
    summary="Compute and store a fresh BrewIQ score",
)
async def compute_score(
    brewery_id: uuid.UUID, session: AsyncSession = SessionDep
) -> BrewIQScoreRead:
    row = await ScoringService(session).compute_and_store(brewery_id)
    return BrewIQScoreRead.from_orm_row(row)


@router.get(
    "/score",
    response_model=BrewIQScoreRead,
    summary="Get the latest stored BrewIQ score",
)
async def get_score(
    brewery_id: uuid.UUID, session: AsyncSession = SessionDep
) -> BrewIQScoreRead:
    await BreweryService(session).get(brewery_id)  # 404 if unknown
    row = await BreweryScoreRepository(session).latest_for_brewery(brewery_id)
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No score computed yet; POST to this endpoint to compute one.",
        )
    return BrewIQScoreRead.from_orm_row(row)
