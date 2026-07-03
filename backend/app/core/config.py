"""Typed application settings loaded from the environment.

Settings are read once and cached (:func:`get_settings`) so the rest of the code
depends on a single, validated configuration object rather than reading
environment variables ad hoc.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Application configuration.

    All fields are populated from ``BREWIQ_``-prefixed environment variables (see
    ``.env.example``). Defaults are safe for local development and tests.
    """

    model_config = SettingsConfigDict(
        env_prefix="BREWIQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Environment = "development"
    log_level: str = "INFO"
    log_json: bool = False

    # Async SQLAlchemy URL. SQLite is used by the test suite via override.
    database_url: str = "postgresql+asyncpg://brewiq:brewiq@localhost:5432/brewiq"
    redis_url: str = "redis://localhost:6379/0"

    # HTTP / discovery tuning.
    http_timeout_seconds: float = 15.0
    http_user_agent: str = (
        "BrewIQBot/0.1 (+https://github.com/micklelow-source/beeriq)"
    )
    discovery_max_concurrency: int = Field(default=5, ge=1, le=50)

    @property
    def is_test(self) -> bool:
        return self.env == "test"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""

    return Settings()
