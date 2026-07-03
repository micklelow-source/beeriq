"""Anthropic-backed AI provider (spec §3, default per ADR-0004).

Uses the Anthropic SDK's structured-outputs helper (``messages.parse``) so the
model's response is validated against the target Pydantic schema before it is
returned. The ``anthropic`` package is imported lazily so the rest of the code —
and the test suite, which uses :class:`FakeAIProvider` — does not require it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.integrations.ai.base import AIExtractionError, SchemaT

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anthropic import AsyncAnthropic

logger = get_logger(__name__)

# Default model. Opus 4.8 uses adaptive-only thinking and rejects sampling
# parameters, so we pass neither temperature nor a thinking budget.
DEFAULT_MODEL = "claude-opus-4-8"


class AnthropicProvider:
    """An :class:`~app.integrations.ai.base.AIProvider` backed by Claude."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 16_000,
        api_key: str | None = None,
    ) -> None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover - exercised only without the dep
            raise AIExtractionError(
                "The 'anthropic' package is required for the Anthropic provider. "
                "Install it or set BREWIQ_AI_PROVIDER=fake."
            ) from exc

        # If api_key is None the SDK resolves ANTHROPIC_API_KEY from the environment.
        self._client: AsyncAnthropic = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def extract(self, prompt: str, *, schema: type[SchemaT]) -> SchemaT:
        response = await self._client.messages.parse(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
        if response.stop_reason == "refusal":
            raise AIExtractionError(
                f"Model refused the extraction request: {response.stop_reason}"
            )
        result = response.parsed_output
        if result is None:
            raise AIExtractionError(
                f"Model returned no valid structured output (stop_reason={response.stop_reason})"
            )
        logger.info(
            "AI extraction complete",
            extra={"model": self._model, "output_tokens": response.usage.output_tokens},
        )
        return result
