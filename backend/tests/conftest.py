"""Shared pytest fixtures.

The suite runs entirely on a temporary SQLite database (via aiosqlite), so no
Postgres/Redis services are required. Environment is configured *before* any
application module is imported so cached settings pick up the test database URL.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

# --- Configure environment before importing the app ---------------------------
_DB_FILE = Path(tempfile.gettempdir()) / f"brewiq_test_{uuid.uuid4().hex}.sqlite3"
os.environ["BREWIQ_ENV"] = "test"
os.environ["BREWIQ_DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_FILE.as_posix()}"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import (  # noqa: E402
    dispose_engine,
    get_engine,
    get_sessionmaker,
)
from app.integrations.fetcher import FetchRequest, FetchResponse  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402


class FakeFetcher:
    """A deterministic in-memory :class:`Fetcher` for tests.

    ``pages`` maps a URL to either a ``FetchResponse`` or the HTML body string
    (wrapped in a 200 response). Unknown URLs return 404 so discovery probing can
    be exercised without network access.
    """

    def __init__(self, pages: dict[str, FetchResponse | str] | None = None) -> None:
        self.pages = pages or {}
        self.requests: list[FetchRequest] = []

    def set(self, url: str, body: FetchResponse | str) -> None:
        self.pages[url] = body

    async def fetch(self, request: FetchRequest) -> FetchResponse:
        self.requests.append(request)
        entry = self.pages.get(request.url)
        if entry is None:
            return FetchResponse(request.url, 404, "", {})
        if isinstance(entry, FetchResponse):
            return entry
        return FetchResponse(request.url, 200, entry, {"content-type": "text/html"})


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    """Create a fresh schema before each test and drop it afterwards."""

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Provide a database session that commits on exit."""

    async with get_sessionmaker()() as sess:
        yield sess
        await sess.commit()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Provide an httpx client bound to the ASGI app (no real network)."""

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def fake_fetcher() -> FakeFetcher:
    return FakeFetcher()


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    """Dispose the engine and remove the temporary database file."""

    import asyncio

    asyncio.run(dispose_engine())
    try:
        _DB_FILE.unlink(missing_ok=True)
    except OSError:
        pass
