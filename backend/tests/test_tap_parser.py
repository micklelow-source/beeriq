"""Tests for heuristic tap-list extraction (spec §3 no-AI path)."""

from __future__ import annotations

import pytest

from app.integrations.ai.heuristic_provider import HeuristicProvider
from app.schemas.extraction import TapListExtraction
from app.services.classifier import content_tap_confidence
from app.services.tap_parser import parse_tap_list


def test_parses_inline_beer_lines() -> None:
    text = (
        "What's on Tap\n"
        "Stoneface IPA  IPA 7.0% ABV\n"
        "Rye Pale Ale — Pale Ale 5.6%\n"
        "Coffee Stout  Stout 6.0%\n"
    )
    result = parse_tap_list(text)
    names = {b.name for b in result.beers}
    assert "Stoneface IPA" in names
    assert "Rye Pale Ale" in names
    ipa = next(b for b in result.beers if b.name == "Stoneface IPA")
    assert ipa.abv == 7.0
    assert ipa.style == "IPA"


def test_parses_card_layout_name_then_style_then_abv() -> None:
    text = "Current Offerings\nHazy Wonder\nHazy IPA\n6.5%\nMidnight\nOatmeal Stout\n5.8%\n"
    result = parse_tap_list(text)
    names = {b.name for b in result.beers}
    assert "Hazy Wonder" in names
    assert "Midnight" in names
    hazy = next(b for b in result.beers if b.name == "Hazy Wonder")
    assert hazy.abv == 6.5


def test_ignores_navigation_and_food_text() -> None:
    text = "Menu\nHome\nAbout\nContact\nHours: 12-9\nFrench Fries\nCheeseburger\n"
    assert parse_tap_list(text).beers == []


def test_deduplicates_and_bounds_abv() -> None:
    text = "IPA One 6.5%\nIPA One 6.5%\nBad Beer 99%\n"  # dupe + implausible ABV
    result = parse_tap_list(text)
    assert sum(b.name == "IPA One" for b in result.beers) == 1
    bad = [b for b in result.beers if b.name == "Bad Beer"]
    # 99% is out of range → dropped as ABV (name still needs a style; "Bad Beer" has none)
    assert bad == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Come see what's on tap this week", 0.9),
        ("Our current offerings change daily", 0.9),
        ("Check out the tap menu", 0.9),
        ("View our food menu", 0.5),
        ("Welcome to our brewery", 0.0),
    ],
)
def test_content_tap_confidence(text: str, expected: float) -> None:
    assert content_tap_confidence(text) == expected


@pytest.mark.asyncio
async def test_heuristic_provider_extracts() -> None:
    provider = HeuristicProvider()
    prompt = "Page text follows:\nHazy Wonder\nHazy IPA\n6.5%\n"
    result = await provider.extract(prompt, schema=TapListExtraction)
    assert any(b.name == "Hazy Wonder" for b in result.beers)
