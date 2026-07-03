"""AI provider protocol and errors."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from app.core.errors import BrewIQError

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AIExtractionError(BrewIQError):
    """Raised when a provider cannot return valid structured output."""


@runtime_checkable
class AIProvider(Protocol):
    """Turns a prompt into a schema-validated Pydantic model.

    Implementations are responsible only for invoking their model and returning a
    validated instance of ``schema``; prompt construction lives in the service
    layer (:class:`app.services.extraction.ExtractionService`). Providers must
    raise :class:`AIExtractionError` rather than return unvalidated data.
    """

    async def extract(self, prompt: str, *, schema: type[SchemaT]) -> SchemaT: ...
