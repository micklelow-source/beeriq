"""Discovered URL ORM model and page-type taxonomy."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brewery import Brewery
    from app.models.page_snapshot import PageSnapshot


class PageType(enum.StrEnum):
    """Classification of a discovered page (spec §1)."""

    TAP = "tap"
    BEER = "beer"
    MENU = "menu"
    EVENTS = "events"
    FOOD_TRUCK = "food_truck"
    HOME = "home"
    UNKNOWN = "unknown"


class DiscoveredURL(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A URL discovered for a brewery, with its classified page type."""

    __tablename__ = "discovered_urls"
    __table_args__ = (
        UniqueConstraint("brewery_id", "url", name="uq_discovered_urls_brewery_url"),
    )

    brewery_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("breweries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    page_type: Mapped[PageType] = mapped_column(
        SAEnum(
            PageType,
            name="page_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=PageType.UNKNOWN,
    )
    # Confidence in the page-type classification, 0.0–1.0.
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    brewery: Mapped[Brewery] = relationship(back_populates="discovered_urls")
    snapshots: Mapped[list[PageSnapshot]] = relationship(
        back_populates="discovered_url",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DiscoveredURL {self.page_type.value} {self.url!r}>"
