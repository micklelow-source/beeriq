"""Deterministic in-memory AI provider for tests and local development.

Returns a preset result when given one, otherwise an empty (schema-default)
instance. Records prompts so tests can assert on prompt construction.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.integrations.ai.base import SchemaT


class FakeAIProvider:
    """An :class:`~app.integrations.ai.base.AIProvider` with no network calls."""

    def __init__(self, result: BaseModel | None = None) -> None:
        self._result = result
        self.prompts: list[str] = []

    async def extract(self, prompt: str, *, schema: type[SchemaT]) -> SchemaT:
        self.prompts.append(prompt)
        if self._result is not None:
            if not isinstance(self._result, schema):
                raise TypeError(
                    f"FakeAIProvider preset is {type(self._result).__name__}, "
                    f"expected {schema.__name__}"
                )
            return self._result
        # Every extraction schema defaults all fields, so this yields a valid,
        # empty result.
        return schema()
