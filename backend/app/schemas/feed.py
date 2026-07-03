"""Live activity feed schemas (spec §8)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

FeedItemKind = Literal["change_event", "score_increase"]


class FeedItem(BaseModel):
    """A single cross-brewery activity item."""

    id: uuid.UUID
    kind: FeedItemKind
    brewery_id: uuid.UUID
    brewery_name: str
    brewery_slug: str
    summary: str
    details: dict[str, Any]
    created_at: datetime


class FeedPage(BaseModel):
    """A paginated slice of the activity feed."""

    items: list[FeedItem]
    total: int
    limit: int
    offset: int
