"""Heuristic (no-AI) extraction provider.

Implements the :class:`AIProvider` interface using the pattern-based tap parser
instead of an LLM, so the discover → scrape → extract pipeline can populate real
tap lists without an API key. Lower quality than the Anthropic provider, but free
and keyless.
"""

from __future__ import annotations

from typing import cast

from app.integrations.ai.base import SchemaT
from app.schemas.extraction import TapListExtraction
from app.services.tap_parser import parse_tap_list


class HeuristicProvider:
    """An :class:`AIProvider` backed by the heuristic tap parser."""

    async def extract(self, prompt: str, *, schema: type[SchemaT]) -> SchemaT:
        if schema is TapListExtraction:
            # The prompt embeds the page text; beer patterns only match content,
            # not the instruction preamble.
            return cast(SchemaT, parse_tap_list(prompt))
        return schema()
