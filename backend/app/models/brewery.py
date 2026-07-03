"""Brewery ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.discovered_url import DiscoveredURL


class Brewery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A physical brewery/taproom that BrewIQ tracks.

    Latitude/longitude are stored as plain floats for now; the PostGIS geometry
    column required by the route planner (spec §7) is introduced in a later
    migration without changing this contract.
    """

    __tablename__ = "breweries"
    __table_args__ = (UniqueConstraint("slug", name="uq_breweries_slug"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    discovered_urls: Mapped[list[DiscoveredURL]] = relationship(
        back_populates="brewery",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Brewery {self.slug!r} ({self.state})>"
