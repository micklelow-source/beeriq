"""Change-event and extraction-result schemas (spec §4)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.change_event import ChangeEventType
from app.schemas.extraction import TapListExtraction


class ChangeEventRead(BaseModel):
    """A detected change as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brewery_id: uuid.UUID
    discovered_url_id: uuid.UUID
    event_type: ChangeEventType
    summary: str
    details: dict[str, Any]
    created_at: datetime


class ChangeEventPage(BaseModel):
    """A paginated list of change events."""

    items: list[ChangeEventRead]
    total: int
    limit: int
    offset: int


class ExtractionResult(BaseModel):
    """The outcome of extracting a page: the data plus detected changes."""

    extraction: TapListExtraction
    changes: list[ChangeEventRead]
