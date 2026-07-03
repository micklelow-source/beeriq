"""Unit tests for pure helpers."""

from __future__ import annotations

from app.core.utils import content_hash, slugify


def test_slugify_is_deterministic_and_url_safe() -> None:
    assert slugify("Smuttynose Brewing Company") == "smuttynose-brewing-company"
    assert slugify("603 Brewery") == "603-brewery"
    assert slugify("  Schilling Beer Co.  ") == "schilling-beer-co"
    assert slugify("Café Malt") == "cafe-malt"


def test_slugify_never_empty() -> None:
    assert slugify("!!!") == "brewery"


def test_content_hash_changes_with_content() -> None:
    assert content_hash("a") == content_hash("a")
    assert content_hash("a") != content_hash("b")
    assert len(content_hash("anything")) == 64
