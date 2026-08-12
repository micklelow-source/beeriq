"""Shared date/time pattern matching used by event_parser.py and
food_truck_parser.py -- both need the same "does this line carry a
day-of-week, month, or numeric date" signal to tell a real entry from
ordinary page text.

Short day/month abbreviations ("sun", "may", "mon", ...) are also common
English words or word fragments ("sun-dried", "we may add...", "salmon"),
so those specific short forms require capitalization -- real schedules
write "Sun" / "May", not "sun-dried" / "salmon may". Full day/month names
("sunday", "march") are long and distinctive enough to stay case-insensitive.
"""

from __future__ import annotations

import re

DAY_RE = re.compile(
    r"\b(?:(?i:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"Mon|Tue|Tues|Wed|Thu|Thur|Thurs|Fri|Sat|Sun)\b"
)
MONTH_RE = re.compile(
    r"\b(?:(?i:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)|May)\b"
)
# "/"-separated only (not "-"): a hyphen between two small numbers is just
# as likely to be a capacity ("40-50 people"), a price range, or a phone
# fragment as an actual date, so it's too weak a signal to trust here.
# Bounded to plausible month/day values so "99/99" can't match either.
NUMERIC_DATE_RE = re.compile(r"\b(?:[1-9]|1[0-2])/(?:[1-9]|[12]\d|3[01])(?:/\d{2,4})?\b")
TIME_RE = re.compile(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", re.IGNORECASE)


def has_date_signal(text: str) -> bool:
    return bool(DAY_RE.search(text) or MONTH_RE.search(text) or NUMERIC_DATE_RE.search(text))
