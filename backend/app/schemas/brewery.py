"""Brewery request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BreweryBase(BaseModel):
    """Fields shared by create/read representations."""

    name: str = Field(min_length=1, max_length=200)
    website: HttpUrl | None = None
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class BreweryCreate(BreweryBase):
    """Payload for creating a brewery. ``slug`` is derived if omitted."""

    slug: str | None = Field(default=None, max_length=200)


class BreweryRead(BreweryBase):
    """Brewery as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime


class BreweryPage(BaseModel):
    """A paginated list of breweries."""

    items: list[BreweryRead]
    total: int
    limit: int
    offset: int
