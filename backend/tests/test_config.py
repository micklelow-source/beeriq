"""Tests for settings normalization."""

from __future__ import annotations

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgres://user:pw@host:5432/db",
            "postgresql+asyncpg://user:pw@host:5432/db",
        ),
        (
            "postgresql://user:pw@host:5432/db",
            "postgresql+asyncpg://user:pw@host:5432/db",
        ),
        # Already has a driver — left untouched.
        (
            "postgresql+asyncpg://user:pw@host:5432/db",
            "postgresql+asyncpg://user:pw@host:5432/db",
        ),
        ("sqlite+aiosqlite:///./var/brewiq.sqlite3", "sqlite+aiosqlite:///./var/brewiq.sqlite3"),
    ],
)
def test_database_url_gets_async_driver(raw: str, expected: str) -> None:
    assert Settings(database_url=raw).database_url == expected


def test_cors_allow_origins_list_parses_and_trims() -> None:
    settings = Settings(cors_allow_origins=" https://a.example , https://b.example")
    assert settings.cors_allow_origins_list == ["https://a.example", "https://b.example"]


def test_cors_allow_origins_list_empty_by_default() -> None:
    assert Settings().cors_allow_origins_list == []
