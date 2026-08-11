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
    text = "Tacos El Rey - Friday\nTacos El Rey - Friday\n"
    result = parse_food_trucks(text)
    assert sum(t.name == "Tacos El Rey" for t in result) == 1
