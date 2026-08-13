"""Tests for the heuristic food-truck schedule parser (no-AI path)."""

from __future__ import annotations

from app.services.food_truck_parser import parse_food_trucks


def test_parses_inline_name_and_schedule() -> None:
    text = (
        "Food Truck Schedule\n"
        "Tacos El Rey - Friday\n"
        "Wood Fired Pizza Co @ Saturday\n"
    )
    result = parse_food_trucks(text)
    names = {t.name for t in result}
    assert "Tacos El Rey" in names
    assert "Wood Fired Pizza Co" in names
    tacos = next(t for t in result if t.name == "Tacos El Rey")
    assert "friday" in (tacos.schedule or "").lower()


def test_parses_card_layout_name_then_schedule() -> None:
    text = "Food Trucks\nThe Grilled Cheese Bus\nThursday 5-9pm\nBBQ Bros\n6/14\n"
    result = parse_food_trucks(text)
    names = {t.name for t in result}
    assert "The Grilled Cheese Bus" in names
    assert "BBQ Bros" in names


def test_ignores_navigation_and_boilerplate() -> None:
    text = "Menu\nHome\nAbout\nContact\nEvents\nCalendar\nFood Truck Schedule\n"
    assert parse_food_trucks(text) == []


def test_requires_schedule_signal_not_just_a_name_like_line() -> None:
    text = "Our Favorite Vendors\nWe love local food\nAnother Line Here\n"
    assert parse_food_trucks(text) == []


def test_deduplicates_by_name() -> None:
    text = "Food Trucks\nTacos El Rey - Friday\nTacos El Rey - Friday\n"
    result = parse_food_trucks(text)
    assert sum(t.name == "Tacos El Rey" for t in result) == 1


def test_requires_the_page_to_mention_food_trucks_at_all() -> None:
    """A page that never says "food truck" anywhere is far more likely to
    be a general events calendar than a food-truck listing -- "Name -
    Weekday" alone isn't enough to conclude otherwise."""

    text = "Tacos El Rey - Friday\nBBQ Bros - Saturday\n"
    assert parse_food_trucks(text) == []


def test_does_not_mistake_menu_items_near_a_lowercase_day_fragment_for_trucks() -> None:
    """Regression: a kitchen menu's "sun" inside "sun-dried" (or similar
    lowercase mid-word fragments) must not read as a Sunday schedule."""

    text = "Cranberry Bog Salad\nWith sun-dried cranberries and goat cheese\n"
    assert parse_food_trucks(text) == []


def test_does_not_mistake_live_music_events_for_food_trucks() -> None:
    """Regression: an events page listing "Live Music by X - Friday" must
    not be read as a food truck named "Live Music by X"."""

    text = "Live music by Busted Stuff - Friday\nLive music by Greg Hall - Saturday\n"
    assert parse_food_trucks(text) == []


def test_does_not_leak_extraction_prompt_preamble() -> None:
    """Regression: HeuristicProvider strips the instruction preamble before
    parsing, but this guards the parser itself against similar boilerplate."""

    text = 'Page text follows:\n"""\nFood Trucks\nTacos El Rey - Friday\n'
    result = parse_food_trucks(text)
    names = {t.name for t in result}
    assert "Page text follows" not in names
    assert "Tacos El Rey" in names
