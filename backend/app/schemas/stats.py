"""Aggregate/statistics schemas (spec §8, map support)."""

from __future__ import annotations

from pydantic import BaseModel


class BreweryStateStat(BaseModel):
    """Brewery count for a single state, used to color-code the map."""

    state: str
    count: int
