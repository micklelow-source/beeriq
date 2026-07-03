# ADR-0004: AI provider abstraction

- Status: Proposed
- Date: 2026-07-02

## Context

The extraction layer (spec §3) converts arbitrary brewery HTML into validated,
structured JSON (beers, styles, ABV/IBU, availability, events, food trucks, hours,
amenities). We must support multiple providers — Anthropic, OpenAI, and local
models — without rewriting extraction logic, and we must never persist unvalidated
model output.

## Decision (proposed)

Introduce an `AIProvider` protocol in `app/integrations/ai/`:

```python
class AIProvider(Protocol):
    async def extract(self, prompt: str, *, schema: type[BaseModel]) -> BaseModel: ...
```

- The provider is responsible only for turning a prompt into a raw response.
- A provider-agnostic `ExtractionService` owns the prompt construction, invokes the
  configured provider, and validates the result against a Pydantic schema before it
  is returned. Validation failure triggers a bounded retry with a repair prompt,
  then a hard error — never silent persistence of malformed data.
- The active provider is selected by configuration (`BREWIQ_AI_PROVIDER`).
- Default to the latest Anthropic Claude models for extraction quality; the
  abstraction keeps swapping providers a config change, not a code change.

## Consequences

- Extraction logic and prompts are written once, provider-independent.
- Costs/latency per provider are measurable behind one seam (feeds spec §11
  monitoring: AI latency).
- Local-model support (self-hosted) fits the same interface for privacy/cost.

## Status note

This ADR is **Proposed**: the interface and `ExtractionService` are not yet
implemented. It is recorded now so the fetcher/scrape pipeline is built with this
seam in mind.
