"""Change-event ORM model and taxonomy (spec §4)."""

from __future__ import annotations

import enum
import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChangeEventType(enum.StrEnum):
    """Kinds of change the diff engine detects between extractions."""

    BEER_ADDED = "beer_added"
    BEER_REMOVED = "beer_removed"
    BEER_ABV_CHANGED = "beer_abv_changed"
    BEER_DESCRIPTION_CHANGED = "beer_description_changed"
    EVENT_ADDED = "event_added"
    EVENT_REMOVED = "event_removed"
    FOOD_TRUCK_ADDED = "food_truck_added"
    FOOD_TRUCK_REMOVED = "food_truck_removed"
    HOURS_CHANGED = "hours_changed"


class ChangeEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single detected change, forming the activity history for a brewery.

    This is the record the live feed (spec §8), scoring (spec §5), and
    notifications (spec §6) build on.
    """

    __tablename__ = "change_events"

    brewery_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("breweries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discovered_url_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("discovered_urls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[ChangeEventType] = mapped_column(
        SAEnum(
            ChangeEventType,
            name="change_event_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ChangeEvent {self.event_type.value}: {self.summary!r}>"
