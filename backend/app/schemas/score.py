"""BrewIQ score schemas (spec §5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.brewery_score import BreweryScore


class ComponentScoreRead(BaseModel):
    name: str
    value: float | None
    available: bool
    weight: float


class TrendRead(BaseModel):
    direction: str
    delta: float | None


class BrewIQScoreRead(BaseModel):
    """A computed BrewIQ score as returned by the API."""

    brewery_id: uuid.UUID
    overall: float
    data_confidence: float
    components: list[ComponentScoreRead]
    recommendations: list[str]
    trend: TrendRead
    computed_at: datetime

    @classmethod
    def from_orm_row(cls, row: BreweryScore) -> BrewIQScoreRead:
        """Build the read model from a persisted :class:`BreweryScore` row."""

        return cls(
            brewery_id=row.brewery_id,
            overall=row.overall,
            data_confidence=row.data_confidence,
            components=[ComponentScoreRead(**c) for c in row.components],
            recommendations=list(row.recommendations),
            trend=TrendRead(direction=row.trend_direction, delta=row.trend_delta),
            computed_at=row.created_at,
        )
