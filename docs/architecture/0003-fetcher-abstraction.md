# ADR-0003: Fetcher abstraction for HTTP and Playwright

- Status: Accepted
- Date: 2026-07-02

## Context

Discovery (spec §1) and scraping (spec §2) both need to retrieve web pages. Many
brewery pages are static HTML retrievable with a simple HTTP client; others are
JavaScript-rendered and require a headless browser (Playwright). The scraper also
needs retry logic, rate limiting, `robots.txt` awareness, conditional requests
(ETag / Last-Modified), and archival — concerns that should not leak into business
logic.

## Decision

Define a minimal `Fetcher` protocol:

```python
class Fetcher(Protocol):
    async def fetch(self, request: FetchRequest) -> FetchResponse: ...
```

Discovery and scraping depend only on this protocol. Two implementations sit
behind it:

- `HttpxFetcher` (implemented now) — fast path for static pages, with conditional
  GET support.
- `PlaywrightFetcher` (planned) — headless-browser rendering for JS-heavy sites,
  plus screenshot/PDF/image capture, injected by the same interface.

Cross-cutting scraper concerns (retries, rate limiting, robots.txt) will be
composed as decorating fetchers wrapping the base implementation, so they apply
uniformly regardless of transport.

## Consequences

- Business logic is tested by injecting a `FakeFetcher` — no network in unit tests.
- The Playwright dependency (and its browser binaries) is isolated to one adapter
  and only loaded where JS rendering is actually required.
- Rate limiting / robots handling can be added without touching discovery or
  scrape services.

## Alternatives considered

- **Call httpx/Playwright directly in services** — couples business logic to
  transport and makes tests require network or a browser; rejected.
