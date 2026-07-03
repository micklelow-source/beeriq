# BrewIQ — Phase 6 Master Specification

> This is the canonical engineering reference for BrewIQ. It captures the full
> target scope. Implementation is incremental; see the "Implementation status"
> table at the end for what is built versus specified.

## Vision

Build BrewIQ into a production-quality SaaS platform that discovers brewery
websites, extracts live tap lists and menus, tracks changes over time, scores
breweries, and serves this via a REST + WebSocket API and a map-based frontend.
Start with New Hampshire; scale nationwide without major architectural change.

Production quality is mandatory: documentation, tests, typing, structured
logging, error handling, and clean architecture. No toy examples, no placeholder
implementations, no TODOs without tracked issues.

## Technology stack

**Backend:** Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16 (+PostGIS),
Redis, Celery, Playwright, Pydantic v2, httpx.

**Frontend:** Next.js 15, React, TypeScript, TailwindCSS, React Query, Leaflet,
OpenStreetMap.

**Infrastructure:** Docker, Docker Compose, Nginx, GitHub Actions, Ubuntu 24.04.

**Testing:** pytest, Playwright, Vitest, GitHub Actions CI.

## Architecture

Clean architecture with dependencies pointing inward.

```
backend/app/  core · models · schemas · repositories · services · integrations · api · seeds · workers · tasks · ai · scheduler · tests
frontend/     app · components · hooks · services · lib · tests
```

Rules: the API layer is transport-only; services hold business logic; repositories
are the only code that talks to the database; integrations wrap all external I/O
(HTTP, browsers, AI providers) behind interfaces so implementations are swappable.

## Feature specifications

### 1. Website Discovery Engine
Given a brewery website, discover tap, beer, menu, events, and food-truck pages by
probing common paths (`/tap`, `/beer`, `/beers`, `/menu`, `/draft`, `/on-tap`,
`/events`, …) and by parsing navigation links. Persist discovered URLs with a
classified page type and confidence.

### 2. Playwright Scraper
Reusable crawler behind the fetcher interface. Retry logic, rate limiting,
`robots.txt` awareness, ETag / Last-Modified conditional requests, content hashing,
screenshot capture, HTML archival, PDF download, image extraction.

### 3. AI Extraction Layer
Provider abstraction over OpenAI, Anthropic, and local models. Converts arbitrary
HTML/text into validated structured JSON: beer name, style, ABV, IBU, availability,
description, seasonal, limited; plus food-truck, events, hours, amenities. Output is
schema-validated before persistence.

### 4. Diff Engine
Compare the latest extraction with the previous one. Detect new/removed beers, ABV
changes, description changes, event changes, food-truck changes, hours changes.
Emit event records and store history.

### 5. BrewIQ Score v2
Components: freshness, tap rotation, beer diversity, event activity, social activity,
website quality, data confidence, historical reliability. Output overall score,
component scores, recommendations, and trend.

### 6. Notification Engine
Channels: email, webhook, (future) push. Triggers: new beer, beer removed, events,
nearby brewery updates, style alerts, radius alerts. Queue-driven workers.

### 7. Route Planner
PostGIS-backed. Input: origin, destination, preferences. Output: optimal brewery
stops, distance off route, estimated arrival, open status, beer matches, food
options, BrewIQ ranking.

### 8. Live Feed
Activity feed (new beer, tap list updated, new event, food truck, score increase)
with pagination.

### 9. WebSockets
FastAPI WebSockets on the backend, React subscriptions on the frontend. Live-update
the map, tap lists, scores, and feed.

### 10. Search
OpenSearch integration over beer name, brewery, style, amenities, dog-friendly,
food trucks, radius, plus natural-language queries
("Dog friendly brewery with hazy IPA near Portsmouth").

### 11. Monitoring
Prometheus + Grafana, health endpoints, metrics for worker status, queue depth, and
API / scraper / AI latency.

### 12. Security
JWT auth, role-based access, API keys, rate limiting, input validation, secrets
management, CSRF where applicable, security headers.

### 13. Testing
Every feature ships with tests. Targets: 90% backend coverage, 80% frontend
coverage, including integration tests.

### 14. Documentation
README, API docs, architecture docs, deployment guide, developer onboarding.

### 15. Git strategy
Commit frequently with conventional-commit messages
(`feat:`, `fix:`, `docs:`, `test:` …).

## Coding standards
Strict typing. No duplicated code. Dependency injection where appropriate.
Repository pattern. Service layer. Structured logging. Meaningful comments.
No placeholder implementations. No TODOs without tracked issues.

## Definition of done
Runs with Docker Compose; imports NH breweries; discovers websites; extracts tap
lists; tracks historical changes; calculates BrewIQ scores; serves a REST API;
provides WebSocket updates; renders breweries on the frontend; supports search;
generates notifications; includes automated tests; deploys via GitHub Actions;
ready for nationwide scaling without major architectural change.

## Implementation status

| # | Subsystem | Status |
|---|-----------|--------|
| — | Repo scaffolding, clean architecture, config, logging, DB | ✅ Implemented |
| 1 | Website Discovery Engine | ✅ Implemented (httpx probing + link parsing) |
| 2 | Scraper / crawler | ◑ Fetcher interface + httpx impl + hashing/snapshots; Playwright impl pending |
| — | NH brewery seed import | ✅ Implemented |
| — | REST API (breweries, discovery, health) | ✅ Implemented |
| — | Test suite (pytest) | ✅ Implemented |
| 3 | AI Extraction Layer | ◑ Provider abstraction + Claude/fake providers + ExtractionService + API; OpenAI/local pending |
| 4 | Diff Engine | ✅ Implemented (pure diff + stored extractions/history + change events + API) |
| 5 | BrewIQ Score v2 | ✅ Implemented (weighted components, data confidence, trend, recommendations, persisted, API); social signal awaits an integration |
| 6 | Notification Engine | ⬚ Specified |
| 7 | Route Planner (PostGIS) | ⬚ Specified |
| 8 | Live Feed | ✅ Implemented (paginated cross-brewery UNION of change events + score increases) |
| 9 | WebSockets | ⬚ Specified |
| 10 | Search (OpenSearch) | ⬚ Specified |
| 11 | Monitoring | ⬚ Specified |
| 12 | Security (JWT/RBAC/API keys) | ⬚ Specified |

Legend: ✅ implemented · ◑ partially implemented · ⬚ specified, not yet built.
