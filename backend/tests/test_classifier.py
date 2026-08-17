"""Unit tests for the pure page-type classifier."""

from __future__ import annotations

import pytest

from app.models.discovered_url import PageType
from app.services.classifier import classify_token, classify_url


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("/on-tap", PageType.TAP),
        ("/tap", PageType.TAP),
        ("/draft", PageType.TAP),
        ("/beers", PageType.BEER),
        ("/beer", PageType.BEER),
        ("/menu", PageType.MENU),
        ("/events", PageType.EVENTS),
        ("/food-truck", PageType.FOOD_TRUCK),
        ("/drinks", PageType.BEER),
        ("/our-drinks", PageType.BEER),
        ("/drink-list", PageType.TAP),
        ("/about", PageType.UNKNOWN),
    ],
)
def test_classify_token(token: str, expected: PageType) -> None:
    page_type, confidence = classify_token(token)
    assert page_type is expected
    if expected is PageType.UNKNOWN:
        assert confidence == 0.0
    else:
        assert confidence > 0.0


def test_food_truck_beats_generic_beer() -> None:
    # A food-truck page should not be misclassified even if "beer" appears nearby.
    page_type, _ = classify_url("https://x.com/food-trucks")
    assert page_type is PageType.FOOD_TRUCK


def test_link_text_can_override_generic_path() -> None:
    # Generic path, descriptive anchor text.
    page_type, confidence = classify_url(
        "https://x.com/page/42", link_text="Our Events Calendar"
    )
    assert page_type is PageType.EVENTS
    assert confidence > 0.0


def test_drinks_link_text_is_recognized() -> None:
    # A "Drinks" nav link (no "beer"/"tap" wording at all) should still surface
    # as a candidate page, not fall through to UNKNOWN.
    page_type, confidence = classify_url("https://x.com/page/7", link_text="Drinks")
    assert page_type is PageType.BEER
    assert confidence > 0.0


@pytest.mark.parametrize(
    "link_text",
    ["Our Brews", "What's Brewing", "Offerings", "Pours", "Flights", "Beverages", "Selections"],
)
def test_additional_brew_vocabulary_is_recognized(link_text: str) -> None:
    # More brewpub-style nav wording, beyond the original tap/beer/menu set --
    # each should surface as a candidate rather than fall through to UNKNOWN.
    page_type, confidence = classify_url("https://x.com/page/9", link_text=link_text)
    assert page_type is not PageType.UNKNOWN
    assert confidence > 0.0


def test_food_truck_still_beats_offerings() -> None:
    # The expanded BEER-ish vocabulary must not steal priority from a clear
    # food-truck signal.
    page_type, _ = classify_url("https://x.com/food-truck-schedule")
    assert page_type is PageType.FOOD_TRUCK
