"""API schema for curated beer festivals / tastings."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.festival import FestivalCategory


class FestivalOut(BaseModel):
    """A festival or tasting event, as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    category: FestivalCategory
    event_date: date | None
    city: str | None
    state: str | None
    description: str | None
    url: str | None
    source: str
