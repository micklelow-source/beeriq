"""Health and readiness endpoints (spec §11)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.api.deps import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return process liveness. Cheap; performs no I/O."""

    return {"status": "ok", "version": __version__}


@router.get("/ready", summary="Readiness probe")
async def ready(session: AsyncSession = SessionDep) -> dict[str, str]:
    """Return readiness, verifying the database connection responds."""

    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
