"""Persisted BrewIQ score (spec §5).

Each computation is stored so trend can be derived from the previous score and
score history is available for the feed and analytics.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BreweryScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single computed BrewIQ score for a brewery."""

    __tablename__ = "brewery_scores"

    brewery_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("breweries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall: Mapped[float] = mapped_column(Float, nullable=False)
    # 0.0–1.0: how much of the intended signal was backed by real data.
    data_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    trend_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    trend_delta: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<BreweryScore brewery={self.brewery_id} overall={self.overall}>"
