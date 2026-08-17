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
    "our-beers",
    "beer-list",
    "draft",
    "drink",
    "drinks",
    "drink-list",
    "our-drinks",
    "brews",
    "our-brews",
    "offerings",
    "beer-offerings",
    "pours",
    "selections",
    "beverage",
    "beverages",
    "flight",
    "flights",
    "whats-brewing",
    "now-brewing",
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
    ("drink list", PageType.TAP, 0.85),
    ("drink-list", PageType.TAP, 0.85),
    ("drinks menu", PageType.TAP, 0.8),
    ("our drinks", PageType.BEER, 0.7),
    ("drinks", PageType.BEER, 0.65),
    ("drink", PageType.BEER, 0.55),
    ("beer offerings", PageType.BEER, 0.75),
    ("beer selections", PageType.BEER, 0.75),
    ("our brews", PageType.BEER, 0.7),
    ("current brews", PageType.BEER, 0.7),
    ("whats-brewing", PageType.BEER, 0.65),
    ("whats brewing", PageType.BEER, 0.65),
    ("what's brewing", PageType.BEER, 0.65),
    ("now-brewing", PageType.BEER, 0.65),
    ("now brewing", PageType.BEER, 0.65),
    ("brews", PageType.BEER, 0.6),
    ("pours", PageType.TAP, 0.6),
    ("flights", PageType.BEER, 0.5),
    ("flight", PageType.BEER, 0.45),
    ("selections", PageType.BEER, 0.5),
    ("offerings", PageType.BEER, 0.55),
    ("beverages", PageType.BEER, 0.5),
    ("beverage", PageType.BEER, 0.45),
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
    "drink list",
    "drinks list",
    "drink menu",
    "what's brewing",
    "whats brewing",
    "now brewing",
    "current brews",
    "our brews",
    "beer selections",
)
# Weaker signals — common but also appear in navigation/boilerplate.
_WEAK_TAP_MARKERS: tuple[str, ...] = (
    "on tap",
    "our beers",
    "our drinks",
    "taproom",
    "tap room",
    "menu",
    "drinks",
    "brews",
    "offerings",
    "selections",
    "pours",
    "flights",
    "beverages",
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
