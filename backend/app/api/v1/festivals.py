"""Curated beer-festival / tasting-event listing."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.repositories.festival import FestivalRepository
from app.schemas.festival import FestivalOut

router = APIRouter(tags=["festivals"])


@router.get(
    "/festivals",
    response_model=list[FestivalOut],
    summary="Upcoming beer festivals and tastings",
)
async def list_festivals(session: AsyncSession = SessionDep) -> list[FestivalOut]:
    festivals = await FestivalRepository(session).list_upcoming(on_or_after=date.today())
    return [FestivalOut.model_validate(f) for f in festivals]
