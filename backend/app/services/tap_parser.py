"""Heuristic tap-list parser (spec §3, no-AI fallback).

Extracts beers (name, style, ABV) from the plain text of a tap/menu page using
pattern matching, so tap lists can be populated by scraping without an AI key.
It handles both inline layouts ("Stoneface IPA · IPA 7.0%") and card layouts
where the name, style, and ABV are on separate lines. It requires a recognized
beer style or an ABV percentage on/near a line, which keeps food-menu and
navigation text from being mistaken for beers.

For JS-rendered sites (whose tap list isn't in the initial HTML) this yields
nothing — those need the Playwright fetcher (spec §2) and/or the AI provider.
"""

from __future__ import annotations

import re

from app.schemas.extraction import BeerExtraction, TapListExtraction

# Longest/most-specific styles first so "double ipa" matches before "ipa".
_STYLE_WORDS: tuple[str, ...] = (
    "new england ipa", "west coast ipa", "hazy double ipa", "double ipa",
    "session ipa", "hazy ipa", "milkshake ipa", "black ipa", "rye ipa",
    "imperial stout", "oatmeal stout", "milk stout", "pastry stout",
    "coffee stout", "india pale ale", "pale ale", "amber ale", "brown ale",
    "blonde ale", "cream ale", "golden ale", "red ale", "wheat ale",
    "belgian ale", "scotch ale", "old ale", "barleywine", "hefeweizen",
    "witbier", "saison", "farmhouse ale", "berliner weisse", "fruited sour",
    "sour ale", "wild ale", "gose", "kölsch", "kolsch", "pilsner", "pilsener",
    "helles", "märzen", "marzen", "oktoberfest", "dunkel", "schwarzbier",
    "vienna lager", "dark lager", "amber lager", "pale lager", "light lager",
    "doppelbock", "baltic porter", "kellerbier", "lambic", "tripel", "dubbel",
    "quad", "porter", "stout", "lager", "bock", "esb", "bitter", "mild",
    "cider", "mead", "seltzer", "ipa", "ale",
)

_ABV_RE = re.compile(r"\b(\d{1,2}(?:\.\d{1,2})?)\s*%")
# Delimiters that separate a beer name from its style/ABV descriptor on one line.
_DELIM_RE = re.compile(r"\s{2,}|\s*[·•|/–—]\s*|\t|\s+-\s+")
# "City, ST" location lines (e.g. "Dover, NH") — never a beer name.
_LOCATION_RE = re.compile(r"^[A-Za-z .'-]+,\s*[A-Z]{2}\.?$")
# Day-of-week / hours lines (e.g. "Sun 12-5").
_HOURS_RE = re.compile(r"\b(mon|tue|wed|thu|fri|sat|sun)\b", re.IGNORECASE)
# Word-boundary style matcher, longest-first, so short styles like "ale" don't
# match inside "Goose"/"Sale" (which broke content matching).
_STYLE_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _STYLE_WORDS) + r")\b", re.IGNORECASE
)

# Lines that are navigation / boilerplate, never beer names.
_BOILERPLATE = (
    "menu", "home", "about", "contact", "events", "hours", "shop", "store",
    "gift card", "merch", "order", "directions", "location", "careers", "jobs",
    "news", "blog", "gallery", "reservation", "catering", "subscribe",
    "newsletter", "sign up", "log in", "login", "cart", "search", "©",
    "copyright", "all rights reserved", "privacy", "terms", "follow us",
    "food truck", "on tap", "tap list", "our beers", "what's on", "taproom",
    "tap room", "read more", "learn more", "view", "close", "draft", "account",
    "faq", "gift", "welcome", "we serve", "we are", "our story", "find us",
    "coming soon", "select option", "add to", "checkout", "wishlist", "brewery",
    "current offering", "offerings", "limit of", "tour", "reserve", "sold out",
    "voted", "award", "take a", "balance of", "sweet and", "our current",
)


def _titlecase_style(style: str) -> str:
    return " ".join(w.upper() if w in {"ipa", "esb"} else w.capitalize() for w in style.split())


def _find_style(text: str) -> str | None:
    m = _STYLE_RE.search(text)
    return m.group(1).lower() if m else None


def _abv(text: str) -> float | None:
    m = _ABV_RE.search(text)
    if not m:
        return None
    value = float(m.group(1))
    return value if 2.0 <= value <= 20.0 else None


def _is_boilerplate(lowered: str) -> bool:
    return any(b in lowered for b in _BOILERPLATE)


def _valid_name(name: str) -> bool:
    if not (2 < len(name) <= 60):
        return False
    if not re.search(r"[A-Za-z]", name):
        return False
    lowered = name.lower()
    if _is_boilerplate(lowered):
        return False
    if lowered in _STYLE_WORDS:  # a bare style is not a beer name
        return False
    if _LOCATION_RE.match(name):  # "Dover, NH"
        return False
    if _HOURS_RE.search(name):  # "Sun 12-5"
        return False
    return True


def _looks_like_name(line: str) -> bool:
    stripped = _LEADING_NUM_RE.sub("", line).strip()
    if not (2 < len(stripped) <= 60) or len(stripped.split()) > 8:
        return False
    if stripped.endswith((".", ",", ":")):  # prose, not a name
        return False
    if not stripped[:1].isupper():
        return False
    return _valid_name(stripped)


def _descriptor(line: str) -> tuple[str | None, float | None]:
    """Return ``(style, abv)`` found on a line (either may be None)."""

    style = _find_style(line.lower())
    return (_titlecase_style(style) if style else None), _abv(line)


def _strip_descriptor(name: str) -> str:
    """Remove a trailing ABV and/or trailing style word from a single-segment name."""

    m = _ABV_RE.search(name)
    if m:
        name = name[: m.start()]
    lowered = name.lower().rstrip()
    for style in _STYLE_WORDS:
        if lowered.endswith(style):
            name = name.rstrip()[: -len(style)]
            break
    return _clean_name(name)


def _inline_beer(line: str) -> BeerExtraction | None:
    """Parse a single line that carries a full entry (name + style/ABV)."""

    parts = [p.strip() for p in _DELIM_RE.split(line) if p.strip()]
    has_abv = _abv(line) is not None
    # Only treat as a complete entry when the name is delimited from the
    # descriptor, or an ABV is present. A bare style line ("Hazy IPA") is not one.
    if len(parts) < 2 and not has_abv:
        return None

    if len(parts) >= 2:
        name = _clean_name(parts[0])
        descriptor = " ".join(parts[1:])
    else:
        name = _strip_descriptor(line)
        descriptor = line

    if not _valid_name(name):
        return None
    style, abv = _descriptor(descriptor)
    if style is None and abv is None:
        return None
    return BeerExtraction(name=name, style=style, abv=abv, availability="on tap")


# Leading list numbering/bullets, e.g. "1. ", "1) ", "1 - ", "2 -Gonic", "- ".
_LEADING_NUM_RE = re.compile(r"^\s*(?:\d{1,3}\s*[.)]|\d{1,3}\s*[-–—]|[-–—•*])\s*")


def _clean_name(raw: str) -> str:
    name = _LEADING_NUM_RE.sub("", raw)
    return name.strip(" -–—:•|\t")


def parse_tap_list(
    text: str, *, max_beers: int = 60, require_abv: bool = True
) -> TapListExtraction:
    """Extract beers from tap/menu page text (best-effort, no AI).

    ``require_abv`` (default) keeps only entries with a plausible ABV percentage,
    which is the strongest signal separating real beers from food-menu items and
    navigation text on messy brewery sites.
    """

    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    beers: list[BeerExtraction] = []
    seen: set[str] = set()
    n = len(lines)

    for i, line in enumerate(lines):
        if len(beers) >= max_beers:
            break
        beer = _inline_beer(line)
        if beer is None and _looks_like_name(line):
            # Card layout: name, then style and/or ABV on the next lines.
            style: str | None = None
            abv: float | None = None
            for j in range(i + 1, min(i + 4, n)):
                if _looks_like_name(lines[j]):
                    break  # next beer's name; descriptor block ended
                s, a = _descriptor(lines[j])
                style = style or s
                abv = abv or a
                if style and abv:
                    break
            if style or abv:
                beer = BeerExtraction(
                    name=_clean_name(line), style=style, abv=abv, availability="on tap"
                )
        if beer is not None:
            if require_abv and beer.abv is None:
                continue
            key = beer.name.lower()
            if key not in seen:
                seen.add(key)
                beers.append(beer)

    return TapListExtraction(beers=beers)
