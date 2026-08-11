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
from app.services.event_parser import parse_events
from app.services.food_truck_parser import parse_food_trucks
from app.services.tap_parser import parse_tap_list


class HeuristicProvider:
    """An :class:`AIProvider` backed by the heuristic parsers.

    Runs all three pattern-based parsers (beers, events, food trucks) over
    every page rather than routing by the page's classified type, since a
    tap-list page can also mention an event, and each parser's own strong
    signal (ABV/style, a date, a schedule) keeps it from picking up content
    that isn't really its own.
    """

    async def extract(self, prompt: str, *, schema: type[SchemaT]) -> SchemaT:
        if schema is TapListExtraction:
            # The prompt embeds the page text; these patterns only match
            # content, not the instruction preamble.
            beers = parse_tap_list(prompt)
            return cast(
                SchemaT,
                beers.model_copy(
                    update={
                        "events": parse_events(prompt),
                        "food_trucks": parse_food_trucks(prompt),
                    }
                ),
            )
        return schema()
