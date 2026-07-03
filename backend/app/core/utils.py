"""Small pure helpers shared across services."""

from __future__ import annotations

import hashlib
import re
import unicodedata

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Return a URL-safe slug for ``value``.

    Normalises accents, lowercases, and collapses non-alphanumerics to single
    hyphens. Deterministic so the same name always yields the same slug.
    """

    normalized = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = _SLUG_STRIP.sub("-", normalized).strip("-")
    return slug or "brewery"


def content_hash(text: str) -> str:
    """Return the SHA-256 hex digest of ``text`` (used for change detection)."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()
