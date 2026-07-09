"""Provider selection based on configuration."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations.ai.base import AIProvider
from app.integrations.ai.fake_provider import FakeAIProvider

logger = get_logger(__name__)


def build_ai_provider(settings: Settings | None = None) -> AIProvider:
    """Return the configured AI provider.

    ``fake`` (the default) needs no credentials and is used in tests and local
    development. ``anthropic`` requires the ``anthropic`` package and an API key.
    ``openai`` / ``local`` are specified (spec §3) but not yet implemented.
    """

    settings = settings or get_settings()
    provider = settings.ai_provider

    if provider == "anthropic":
        # Imported here so the dependency is only required when actually selected.
        from app.integrations.ai.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            model=settings.ai_model,
            max_tokens=settings.ai_max_tokens,
            api_key=settings.anthropic_api_key,
        )

    if provider == "heuristic":
        from app.integrations.ai.heuristic_provider import HeuristicProvider

        return HeuristicProvider()

    if provider in {"openai", "local"}:
        raise NotImplementedError(
            f"AI provider {provider!r} is specified in the roadmap (spec §3, ADR-0004) "
            "but not yet implemented; use 'anthropic' or 'fake'."
        )

    if provider != "fake":
        logger.warning("Unknown AI provider; falling back to fake", extra={"provider": provider})
    return FakeAIProvider()
