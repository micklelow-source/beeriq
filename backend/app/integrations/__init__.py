"""External I/O adapters (HTTP fetching now; Playwright / AI providers later)."""

from app.integrations.fetcher import (
    Fetcher,
    FetchRequest,
    FetchResponse,
    HttpxFetcher,
)

__all__ = ["Fetcher", "FetchRequest", "FetchResponse", "HttpxFetcher"]
