"""Beer-festival / tasting-event ORM model.

Distinct from brewery-hosted events (``EventExtraction``, scraped per
brewery website): festivals are standalone calendar entries curated from
external listings (e.g. beerfests.com) and are not always hosted by, or
attached to, a single brewery already in the directory -- hence their own
table rather than being shoehorned onto a ``Brewery`` row.
"""

from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FestivalCategory(enum.StrEnum):
    """Kind of curated beer event."""

    FESTIVAL = "festival"
    TASTING = "tasting"


class Festival(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A beer festival or tasting event, curated from external listings."""

    __tablename__ = "festivals"
    __table_args__ = (UniqueConstraint("slug", name="uq_festivals_slug"),)

    slug: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[FestivalCategory] = mapped_column(
        SAEnum(
            FestivalCategory,
            name="festival_category",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=FestivalCategory.FESTIVAL,
    )
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="beerfests.com")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Festival {self.slug!r} ({self.event_date})>"
