"""Persisted AI extraction result (spec §4 — history)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Extraction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A stored structured extraction for a discovered URL.

    ``payload`` is the JSON-serialized :class:`~app.schemas.extraction.TapListExtraction`.
    Keeping every extraction gives the diff engine a "previous" to compare against
    and preserves history for scoring and trends.
    """

    __tablename__ = "extractions"

    discovered_url_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("discovered_urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Extraction url={self.discovered_url_id} at={self.created_at}>"
