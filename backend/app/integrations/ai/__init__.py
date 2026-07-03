"""AI provider abstraction (spec §3, ADR-0004).

Extraction logic depends on the :class:`AIProvider` protocol, not on any single
vendor SDK. Providers are selected by configuration via :func:`build_ai_provider`.
"""

from app.integrations.ai.base import AIExtractionError, AIProvider
from app.integrations.ai.factory import build_ai_provider
from app.integrations.ai.fake_provider import FakeAIProvider

__all__ = [
    "AIProvider",
    "AIExtractionError",
    "FakeAIProvider",
    "build_ai_provider",
]
