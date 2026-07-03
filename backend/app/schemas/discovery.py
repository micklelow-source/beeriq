"""Discovery and snapshot schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.discovered_url import PageType


class DiscoveredURLRead(BaseModel):
    """A discovered URL as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brewery_id: uuid.UUID
    url: str
    page_type: PageType
    confidence: float
    created_at: datetime


class DiscoveryResult(BaseModel):
    """Outcome of running discovery for a brewery."""

    brewery_id: uuid.UUID
    discovered: list[DiscoveredURLRead]
    probed: int


class PageSnapshotRead(BaseModel):
    """A stored page snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    discovered_url_id: uuid.UUID
    status_code: int
    content_hash: str
    etag: str | None
    last_modified: str | None
    created_at: datetime


class ScrapeResult(BaseModel):
    """Outcome of scraping a discovered URL."""

    snapshot: PageSnapshotRead
    changed: bool
