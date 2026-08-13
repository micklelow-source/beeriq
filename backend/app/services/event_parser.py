"""Heuristic events parser (no-AI fallback), same spirit as tap_parser.py.

Extracts events (title, date-as-written) from the plain text of an events/
calendar page using pattern matching. Requires a recognizable date token
(a day-of-week name, a month name, or a numeric MM/DD date) near a
title-like line -- that's the strong signal separating real events from
navigation and boilerplate text, mirroring how tap_parser requires an ABV
or known style word before trusting a line is a beer.

Real limits (same caveat as tap_parser): a page whose events live in a
JS-rendered calendar widget or an embedded iframe (Eventbrite, Google
Calendar, ...) won't have that content in the initial HTML, so this yields
nothing for those -- they'd need the AI provider instead.
"""

from __future__ import annotations

import re

from app.schemas.extraction import EventExtraction
from app.services._date_signals import DAY_RE, MONTH_RE, NUMERIC_DATE_RE, TIME_RE, has_date_signal

# Delimiters that separate a title from its date on one line.
_DELIM_RE = re.compile(r"\s*[·•|]\s*|\s{2,}|\s+-\s+|\s+@\s+")
_LEADING_NUM_RE = re.compile(r"^\s*(?:\d{1,3}\s*[.)]|[-–—•*])\s*")

# Deliberately does NOT include "beer" -- brewery event titles legitimately
# contain it ("Fall Beer Fest", "New Release Party", ...); the date-signal
# requirement is the real filter against nav/boilerplate, this list only
# catches specific known nav-link text.
_BOILERPLATE = (
    "home", "about", "contact us", "our beers", "beer menu", "shop", "store",
    "gift card", "merch", "order online", "directions", "location",
    "careers", "jobs", "news", "blog", "gallery", "reservation", "catering",
    "subscribe", "newsletter", "sign up", "log in", "login", "cart", "search",
    "©", "copyright", "all rights reserved", "privacy", "terms", "follow us",
    "taproom", "tap room", "read more", "learn more", "close", "account",
    "faq", "welcome", "our story", "find us", "buy tickets", "get tickets",
    "see all events", "past events", "load more", "subscribe to our",
    "page text follows",
    # Common UI chrome on calendar/listing widgets, not an event title.
    "clear filter", "more info", "show more", "filter by", "sort by",
    "next event", "previous event", "add to calendar",
)


def _is_boilerplate(lowered: str) -> bool:
    return any(b in lowered for b in _BOILERPLATE)


def _clean(raw: str) -> str:
    return _LEADING_NUM_RE.sub("", raw).strip(" -–—:•|\t")


def _valid_title(title: str) -> bool:
    if not (2 < len(title) <= 100):
        return False
    if not re.search(r"[A-Za-z]", title):
        return False
    lowered = title.lower()
    if _is_boilerplate(lowered):
        return False
    if title.endswith((".", ",")):  # prose, not a title
        return False
    return True


def _looks_like_title(line: str) -> bool:
    stripped = _clean(line)
    if not (2 < len(stripped) <= 100) or len(stripped.split()) > 12:
        return False
    if not stripped[:1].isupper():
        return False
    return _valid_title(stripped)


def _extract_date_part(line: str) -> str | None:
    """Pull just the date/time-ish portion out of a line for the ``date`` field."""

    parts = []
    for m in (DAY_RE, MONTH_RE, NUMERIC_DATE_RE, TIME_RE):
        found = m.search(line)
        if found:
            parts.append(found.group(0))
    return " ".join(parts) if parts else None


def parse_events(text: str, *, max_events: int = 30) -> list[EventExtraction]:
    """Extract events from events/calendar page text (best-effort, no AI)."""

    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    events: list[EventExtraction] = []
    seen: set[str] = set()
    n = len(lines)

    for i, line in enumerate(lines):
        if len(events) >= max_events:
            break

        title: str | None = None
        date: str | None = None

        if has_date_signal(line):
            parts = [p.strip() for p in _DELIM_RE.split(line) if p.strip()]
            non_date_parts = [p for p in parts if not has_date_signal(p)]
            if non_date_parts and _valid_title(non_date_parts[0]):
                title = _clean(non_date_parts[0])
                date = _extract_date_part(line)
        elif _looks_like_title(line):
            # Card layout: title, then a date line follows within a few lines.
            for j in range(i + 1, min(i + 4, n)):
                if _looks_like_title(lines[j]) and not has_date_signal(lines[j]):
                    break  # next event's title; this one had no date
                if has_date_signal(lines[j]):
                    title = _clean(line)
                    date = _extract_date_part(lines[j])
                    break

        if title and _valid_title(title):
            key = title.lower()
            if key not in seen:
                seen.add(key)
                events.append(EventExtraction(title=title, date=date))

    return events
