"""Tests for the heuristic events parser (no-AI path)."""

from __future__ import annotations

from app.services.event_parser import parse_events


def test_parses_inline_title_and_date() -> None:
    text = (
        "Upcoming Events\n"
        "Trivia Night - Wednesday 7pm\n"
        "Live Music @ Saturday\n"
    )
    result = parse_events(text)
    titles = {e.title for e in result}
    assert "Trivia Night" in titles
    assert "Live Music" in titles
    trivia = next(e for e in result if e.title == "Trivia Night")
    assert "wednesday" in (trivia.date or "").lower()


def test_parses_card_layout_title_then_date() -> None:
    text = "Events\nFall Beer Fest\nSaturday, October 12\nOktoberfest Party\nSep 20\n"
    result = parse_events(text)
    titles = {e.title for e in result}
    assert "Fall Beer Fest" in titles
    assert "Oktoberfest Party" in titles


def test_ignores_navigation_and_boilerplate() -> None:
    text = "Menu\nHome\nAbout\nContact\nBuy Tickets\nSee All Events\nHours\n"
    assert parse_events(text) == []


def test_requires_date_signal_not_just_a_titlecase_line() -> None:
    # A title-like line with no date anywhere nearby should not become an event.
    text = "Our Brewery Story\nWe have been brewing since forever\nAnother Line Here\n"
    assert parse_events(text) == []


def test_deduplicates_by_title() -> None:
    text = "Trivia Night - Monday\nTrivia Night - Monday\n"
    result = parse_events(text)
    assert sum(e.title == "Trivia Night" for e in result) == 1
