"""Heuristic food-truck schedule parser (no-AI fallback), same spirit as
tap_parser.py and event_parser.py.

Extracts food trucks (vendor name, schedule-as-written) from the plain text
of a food-truck/events page. Requires a day-of-week or date signal near a
name-like line -- food truck schedules are almost always "Vendor Name --
Wednesday" or "Vendor Name -- 6/12".

That alone isn't a reliable enough signal on its own, though: a general
events page lists plenty of "Name - Weekday" entries that are trivia
nights, live bands, or book clubs, not food trucks. So this also requires
the phrase "food truck" to appear *somewhere* on the page before trusting
any per-line matches at all -- a real food-truck listing almost always
says so (a section header, the page title, "This Week's Food Trucks", ...),
while a page that never says it is far more likely to be a general events
calendar this parser has no business drawing conclusions from.

Same real limits as the other heuristic parsers: JS-rendered widgets and
embedded booking iframes won't be in the initial HTML.
"""

from __future__ import annotations

import re

from app.schemas.extraction import FoodTruckExtraction
from app.services._date_signals import DAY_RE, NUMERIC_DATE_RE, has_date_signal

_FOOD_TRUCK_MENTION_RE = re.compile(r"food\s*truck", re.IGNORECASE)

_DELIM_RE = re.compile(r"\s*[·•|]\s*|\s{2,}|\s+-\s+|\s+@\s+")
_LEADING_NUM_RE = re.compile(r"^\s*(?:\d{1,3}\s*[.)]|[-–—•*])\s*")

_BOILERPLATE = (
    "menu", "home", "about", "contact", "beer", "beers", "on tap", "tap list",
    "shop", "store", "gift card", "merch", "order", "directions", "location",
    "careers", "jobs", "news", "blog", "gallery", "reservation", "catering",
    "subscribe", "newsletter", "sign up", "log in", "login", "cart", "search",
    "©", "copyright", "all rights reserved", "privacy", "terms", "follow us",
    "events", "calendar", "taproom", "tap room", "read more", "learn more",
    "view", "close", "account", "faq", "welcome", "our story", "find us",
    "food truck schedule", "weekly schedule", "food trucks",
    # These pages are commonly shared with an events listing; without this,
    # a "Live Music by X - Friday" event line reads exactly like a food
    # truck entry to this parser's name+date heuristic.
    "live music", "trivia", "bingo", "karaoke", "open mic", "comedy night",
    "concert", "get tickets", "buy tickets", "rsvp", "page text follows",
    # Common UI chrome on calendar/listing widgets, not a vendor name.
    "clear filter", "more info", "load more", "show more", "filter by",
    "sort by", "next event", "previous event", "add to calendar",
)


def _is_boilerplate(lowered: str) -> bool:
    return any(b in lowered for b in _BOILERPLATE)


def _clean(raw: str) -> str:
    return _LEADING_NUM_RE.sub("", raw).strip(" -–—:•|\t")


def _valid_name(name: str) -> bool:
    if not (2 < len(name) <= 60) or len(name.split()) > 8:
        return False
    if not re.search(r"[A-Za-z]", name):
        return False
    if _is_boilerplate(name.lower()):
        return False
    if name.endswith((".", ",")):
        return False
    return True


def _looks_like_name(line: str) -> bool:
    stripped = _clean(line)
    if not _valid_name(stripped):
        return False
    return stripped[:1].isupper()


def _extract_schedule_part(line: str) -> str | None:
    parts = []
    for m in (DAY_RE, NUMERIC_DATE_RE):
        found = m.search(line)
        if found:
            parts.append(found.group(0))
    return " ".join(parts) if parts else None


def parse_food_trucks(text: str, *, max_trucks: int = 20) -> list[FoodTruckExtraction]:
    """Extract food trucks from a page's text (best-effort, no AI)."""

    if not _FOOD_TRUCK_MENTION_RE.search(text):
        return []

    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    trucks: list[FoodTruckExtraction] = []
    seen: set[str] = set()
    n = len(lines)

    for i, line in enumerate(lines):
        if len(trucks) >= max_trucks:
            break

        name: str | None = None
        schedule: str | None = None

        if has_date_signal(line):
            parts = [p.strip() for p in _DELIM_RE.split(line) if p.strip()]
            non_date_parts = [p for p in parts if not has_date_signal(p)]
            if non_date_parts and _valid_name(non_date_parts[0]):
                name = _clean(non_date_parts[0])
                schedule = _extract_schedule_part(line)
        elif _looks_like_name(line):
            for j in range(i + 1, min(i + 3, n)):
                if _looks_like_name(lines[j]) and not has_date_signal(lines[j]):
                    break  # next truck's name; this one had no schedule
                if has_date_signal(lines[j]):
                    name = _clean(line)
                    schedule = _extract_schedule_part(lines[j])
                    break

        if name and _valid_name(name):
            key = name.lower()
            if key not in seen:
                seen.add(key)
                trucks.append(FoodTruckExtraction(name=name, schedule=schedule))

    return trucks
