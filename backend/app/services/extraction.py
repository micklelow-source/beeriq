"""AI extraction service (spec §3).

Owns prompt construction and orchestrates a provider-agnostic extraction. The
provider (Claude by default) validates its output against
:class:`TapListExtraction` before returning it, so this service always yields a
schema-valid result or raises :class:`AIExtractionError`.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.core.utils import html_to_text
from app.integrations.ai.base import AIProvider
from app.schemas.extraction import TapListExtraction

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = """\
You extract structured brewery information from the text of a brewery web page.
Only use information present in the text — never invent beers, events, or details.
If the page has no relevant content for a field, return an empty list or null.

Extract:
- beers: each with name, style, ABV, IBU, availability, description, and whether
  it is seasonal or a limited release.
- food_trucks: any scheduled food trucks or vendors.
- events: title, date (as written), and description.
- hours: the taproom's opening hours, as written.
- amenities: notable features (e.g. "dog friendly", "outdoor seating", "food").

Page text follows:
"""


class ExtractionService:
    """Extracts a :class:`TapListExtraction` from brewery page HTML."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def extract_from_html(self, html: str) -> TapListExtraction:
        """Extract structured data from a page's raw HTML."""

        text = html_to_text(html)
        if not text:
            logger.info("Page had no extractable text; returning empty result")
            return TapListExtraction()
        prompt = f"{_SYSTEM_INSTRUCTION}\n\"\"\"\n{text}\n\"\"\""
        return await self.provider.extract(prompt, schema=TapListExtraction)
