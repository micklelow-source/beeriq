"""Shared date/time pattern matching used by event_parser.py and
food_truck_parser.py -- both need the same "does this line carry a
day-of-week, month, or numeric date" signal to tell a real entry from
ordinary page text."""

from __future__ import annotations

import re

DAY_RE = re.compile(
    r"\b(mon(day)?|tue(s|sday)?|wed(nesday)?|thu(rs|rsday)?|fri(day)?|"
    r"sat(urday)?|sun(day)?)s?\b",
    re.IGNORECASE,
)
MONTH_RE = re.compile(
    r"\b(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?|aug(ust)?|"
    r"sep(t|tember)?|oct(ober)?|nov(ember)?|dec(ember)?)\b",
    re.IGNORECASE,
)
NUMERIC_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")
TIME_RE = re.compile(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", re.IGNORECASE)


def has_date_signal(text: str) -> bool:
    return bool(DAY_RE.search(text) or MONTH_RE.search(text) or NUMERIC_DATE_RE.search(text))
