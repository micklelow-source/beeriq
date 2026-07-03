"""Small pure helpers shared across services."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from html.parser import HTMLParser

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")


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


class _TextExtractor(HTMLParser):
    """Collect visible text, dropping ``<script>``/``<style>`` content."""

    _SKIP = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._parts.append(data)

    @property
    def text(self) -> str:
        return "\n".join(self._parts)


def html_to_text(html: str, *, max_chars: int = 20_000) -> str:
    """Reduce HTML to normalized visible text, truncated to ``max_chars``.

    Feeding plain text to the AI extractor (spec §3) rather than raw markup cuts
    token usage sharply and removes boilerplate that distracts the model.
    """

    extractor = _TextExtractor()
    extractor.feed(html)
    text = _WHITESPACE.sub(" ", extractor.text)
    text = _BLANK_LINES.sub("\n\n", text).strip()
    return text[:max_chars]
