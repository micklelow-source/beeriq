"""Live activity feed endpoint (spec §8)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.schemas.feed import FeedPage
from app.services.feed import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get(
    "",
    response_model=FeedPage,
    summary="Cross-brewery activity feed (newest first)",
)
async def get_feed(
    session: AsyncSession = SessionDep,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FeedPage:
    items, total = await FeedService(session).page(limit=limit, offset=offset)
    return FeedPage(items=items, total=total, limit=limit, offset=offset)
