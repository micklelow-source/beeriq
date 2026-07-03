"""FastAPI dependencies.

The request-scoped session commits when the handler returns successfully and rolls
back on any exception, so handlers and services never manage transactions
themselves.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_sessionmaker
from app.integrations.ai import AIProvider, build_ai_provider
from app.integrations.fetcher import Fetcher, HttpxFetcher


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a transactional database session for the duration of a request."""

    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_fetcher() -> AsyncIterator[Fetcher]:
    """Yield an HTTP fetcher, closed when the request completes."""

    fetcher = HttpxFetcher()
    try:
        yield fetcher
    finally:
        await fetcher.aclose()


def get_ai_provider() -> AIProvider:
    """Return the configured AI extraction provider (spec §3)."""

    return build_ai_provider()


SessionDep = Depends(get_session)
FetcherDep = Depends(get_fetcher)
AIProviderDep = Depends(get_ai_provider)
