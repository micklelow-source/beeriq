"""Async database engine and session management.

A single engine is created lazily from settings. Sessions are provided through
:func:`session_scope` (an async context manager that commits on success and rolls
back on error) and the FastAPI dependency in :mod:`app.api.deps`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _build_engine(settings: Settings) -> AsyncEngine:
    # ``check_same_thread`` is only meaningful for SQLite (tests); passing connect
    # args unconditionally is harmless because SQLAlchemy filters by dialect.
    connect_args: dict[str, bool | str | int] = {}
    is_sqlite = settings.database_url.startswith("sqlite")
    if is_sqlite:
        connect_args["check_same_thread"] = False
        # SQLite's default rollback-journal mode serializes ALL writers (a
        # writer blocks every other reader/writer), so any concurrent scrape
        # script -- writing to many different breweries from many isolated
        # sessions at once, by design -- hits "database is locked" almost
        # immediately. WAL mode lets readers and writers coexist; the
        # generous busy_timeout below covers the remaining writer-vs-writer
        # case by waiting instead of failing outright. Postgres (production)
        # handles this natively and needs neither.
        connect_args["timeout"] = 30
    elif settings.is_production and settings.database_url.startswith("postgresql"):
        # Managed Postgres providers (Render, ...) reject plaintext connections;
        # asyncpg needs this passed as a connect arg, not a URL query param.
        connect_args["ssl"] = "require"
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )
    if is_sqlite:
        @event.listens_for(engine.sync_engine, "connect")
        def _enable_wal(dbapi_connection, _record):  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

    return engine


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, creating it on first use."""

    global _engine
    if _engine is None:
        _engine = _build_engine(get_settings())
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide async session factory."""

    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional session: commit on success, rollback on error."""

    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Dispose the engine (used on shutdown and in test teardown)."""

    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
