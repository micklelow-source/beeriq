"""Heuristic food-truck schedule parser (no-AI fallback), same spirit as
tap_parser.py and event_parser.py.

Extracts food trucks (vendor name, schedule-as-written) from the plain text
of a food-truck/events page. Requires a day-of-week or date signal near a
name-like line -- food truck schedules are almost always "Vendor Name --
Wednesday" or "Vendor Name -- 6/12", which is a strong enough signal to
avoid mistaking regular menu items or navigation text for a truck.

Same real limits as the other heuristic parsers: JS-rendered widgets and
embedded booking iframes won't be in the initial HTML.
"""

from __future__ import annotations

import re

from app.schemas.extraction import FoodTruckExtraction
from app.services._date_signals import DAY_RE, NUMERIC_DATE_RE, has_date_signal

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
