"""Page snapshot ORM model — the archival unit produced by the scraper."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.discovered_url import DiscoveredURL


class PageSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single fetch of a discovered URL.

    ``content_hash`` lets the diff engine (spec §4) and scheduler skip unchanged
    pages. ``etag`` / ``last_modified`` support conditional requests (spec §2).
    """

    __tablename__ = "page_snapshots"

    discovered_url_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("discovered_urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    html: Mapped[str | None] = mapped_column(Text, nullable=True)
    etag: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(64), nullable=True)

    discovered_url: Mapped[DiscoveredURL] = relationship(back_populates="snapshots")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PageSnapshot {self.content_hash[:8]} status={self.status_code}>"
