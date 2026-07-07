"""Cross-brewery directory listings for the events and food-truck pages."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class _BreweryRef(BaseModel):
    """The brewery an activity belongs to."""

    brewery_id: uuid.UUID
    brewery_name: str
    brewery_slug: str
    brewery_state: str | None


class BreweryEvent(_BreweryRef):
    """A current event at a brewery (spec §8, events page)."""

    title: str
    date: str | None
    description: str | None


class BreweryFoodTruck(_BreweryRef):
    """A current food truck at a brewery (spec §8, food-truck page)."""

    name: str
    schedule: str | None
