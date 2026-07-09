"""Pure page-type classification used by the discovery engine.

Kept dependency-free and side-effect-free so it can be unit-tested in isolation
and reused by both path-probing and link-parsing code paths.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.models.discovered_url import PageType

# Candidate paths probed on every brewery site (spec §1). Ordered roughly by how
# commonly they appear.
CANDIDATE_PATHS: tuple[str, ...] = (
    "tap",
    "taps",
    "on-tap",
    "ontap",
    "beer",
    "beers",
    "draft",
    "menu",
    "menus",
    "events",
    "calendar",
    "food-truck",
    "food-trucks",
)

# Keyword → (page type, confidence). Longer/more specific keywords first so, e.g.,
# "food truck" wins over a bare "food". Confidence reflects how strongly the token
# implies the page type.
_KEYWORD_RULES: tuple[tuple[str, PageType, float], ...] = (
    ("food-truck", PageType.FOOD_TRUCK, 0.9),
    ("food truck", PageType.FOOD_TRUCK, 0.9),
    ("foodtruck", PageType.FOOD_TRUCK, 0.85),
    ("on-tap", PageType.TAP, 0.9),
    ("on tap", PageType.TAP, 0.9),
    ("tap", PageType.TAP, 0.8),
    ("draft", PageType.TAP, 0.75),
    ("draught", PageType.TAP, 0.75),
    ("beers", PageType.BEER, 0.8),
    ("beer", PageType.BEER, 0.7),
    ("menu", PageType.MENU, 0.75),
    ("events", PageType.EVENTS, 0.85),
    ("event", PageType.EVENTS, 0.7),
    ("calendar", PageType.EVENTS, 0.6),
)


# Phrases in a page's *content* that strongly indicate a live tap list, so a page
# is classified as TAP even when its URL/link text is generic (e.g. "/menu").
_STRONG_TAP_MARKERS: tuple[str, ...] = (
    "what's on tap",
    "whats on tap",
    "what's pouring",
    "whats pouring",
    "currently on tap",
    "current offerings",
    "current taps",
    "current beers",
    "on tap now",
    "now pouring",
    "currently pouring",
    "tap list",
    "tap menu",
    "beer menu",
    "draft list",
    "draught list",
    "beers on tap",
    "on draft",
)
# Weaker signals — common but also appear in navigation/boilerplate.
_WEAK_TAP_MARKERS: tuple[str, ...] = (
    "on tap",
    "our beers",
    "taproom",
    "tap room",
    "menu",
)


def classify_token(token: str) -> tuple[PageType, float]:
    """Classify an arbitrary token (a URL path segment or link text)."""

    lowered = token.strip().lower()
    for keyword, page_type, confidence in _KEYWORD_RULES:
        if keyword in lowered:
            return page_type, confidence
    return PageType.UNKNOWN, 0.0


def content_tap_confidence(text: str) -> float:
    """Confidence that a page's *body text* is a tap list (0.0–0.9).

    Strong phrases ("what's on tap", "current offerings", "tap menu", …) score
    high; weaker ones ("on tap", "menu") score lower.
    """

    lowered = text.lower()
    if any(marker in lowered for marker in _STRONG_TAP_MARKERS):
        return 0.9
    if any(marker in lowered for marker in _WEAK_TAP_MARKERS):
        return 0.5
    return 0.0


def classify_url(url: str, *, link_text: str = "") -> tuple[PageType, float]:
    """Classify a URL using its path and, optionally, its anchor text.

    The higher-confidence signal between the path and the link text wins, so a
    generic path with descriptive link text (or vice versa) is still classified.
    """

    path = urlparse(url).path
    best_type, best_conf = classify_token(path)
    if link_text:
        text_type, text_conf = classify_token(link_text)
        if text_conf > best_conf:
            best_type, best_conf = text_type, text_conf
    return best_type, best_conf
