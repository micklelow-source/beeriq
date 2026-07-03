"""Fetcher abstraction.

Discovery and scraping depend on the :class:`Fetcher` protocol rather than on
httpx or Playwright directly. This keeps business logic testable (inject a fake
fetcher) and lets the Playwright crawler (spec §2) be dropped in later behind the
same interface. See ADR-0003.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import httpx

from app.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class FetchRequest:
    """A request to fetch a single URL.

    ``etag`` / ``last_modified`` enable conditional GETs so unchanged pages return
    ``304`` and save bandwidth (spec §2).
    """

    url: str
    method: str = "GET"
    etag: str | None = None
    last_modified: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FetchResponse:
    """The result of a fetch."""

    url: str
    status_code: int
    text: str
    headers: dict[str, str]

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def not_modified(self) -> bool:
        return self.status_code == 304

    @property
    def etag(self) -> str | None:
        return self.headers.get("etag")

    @property
    def last_modified(self) -> str | None:
        return self.headers.get("last-modified")


@runtime_checkable
class Fetcher(Protocol):
    """Something that can fetch a URL and return a :class:`FetchResponse`."""

    async def fetch(self, request: FetchRequest) -> FetchResponse: ...


class HttpxFetcher:
    """A :class:`Fetcher` backed by httpx with sane defaults and conditional GETs.

    A single :class:`httpx.AsyncClient` is reused for connection pooling. Callers
    should use the fetcher as an async context manager, or call :meth:`aclose`.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = httpx.AsyncClient(
            timeout=self._settings.http_timeout_seconds,
            headers={"User-Agent": self._settings.http_user_agent},
            follow_redirects=True,
        )

    async def fetch(self, request: FetchRequest) -> FetchResponse:
        headers = dict(request.headers)
        if request.etag:
            headers["If-None-Match"] = request.etag
        if request.last_modified:
            headers["If-Modified-Since"] = request.last_modified

        response = await self._client.request(
            request.method, request.url, headers=headers
        )
        return FetchResponse(
            url=str(response.url),
            status_code=response.status_code,
            text=response.text,
            headers={k.lower(): v for k, v in response.headers.items()},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HttpxFetcher:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
