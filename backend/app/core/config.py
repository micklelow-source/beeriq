"""Typed application settings loaded from the environment.

Settings are read once and cached (:func:`get_settings`) so the rest of the code
depends on a single, validated configuration object rather than reading
environment variables ad hoc.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
AIProviderName = Literal["fake", "heuristic", "anthropic", "openai", "local"]


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

    # Comma-separated origins allowed to call the API in production (e.g. the
    # deployed frontend's URL). Ignored outside production, where all origins
    # are allowed for local/dev convenience.
    cors_allow_origins: str = ""

    # HTTP / discovery tuning.
    http_timeout_seconds: float = 15.0
    http_user_agent: str = (
        "BrewIQBot/0.1 (+https://github.com/micklelow-source/beeriq)"
    )
    discovery_max_concurrency: int = Field(default=5, ge=1, le=50)

    # AI extraction (spec §3). Defaults to the credential-free fake provider so
    # the app runs out of the box; set to "anthropic" with a key for real use.
    ai_provider: AIProviderName = "fake"
    ai_model: str = "claude-opus-4-8"
    ai_max_tokens: int = Field(default=16_000, ge=256, le=128_000)
    anthropic_api_key: str | None = None

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Rewrite driverless ``postgres(ql)://`` URLs to the asyncpg driver.

        Managed Postgres providers (Render, Heroku, ...) hand out plain libpq
        URLs, but ``create_async_engine`` requires an async driver in the scheme.
        """

        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix) :]
        return value

    @property
    def is_test(self) -> bool:
        return self.env == "test"

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""

    return Settings()
