# ADR-0001: Clean architecture layering

- Status: Accepted
- Date: 2026-07-02

## Context

BrewIQ starts as a New Hampshire MVP but must scale to a nationwide platform with
many subsystems (discovery, scraping, AI extraction, scoring, notifications,
routing, search) without structural rewrites. Uncontrolled coupling between HTTP
handling, business logic, and data access is the most common reason such systems
become unmaintainable.

## Decision

Organise the backend into concentric layers with dependencies pointing inward:

```
api  →  services  →  repositories  →  models
                ↘  integrations (external I/O behind interfaces)
```

- **api/** — FastAPI routers. Transport only: parse/validate requests, call a
  service, serialise the result, map domain errors to HTTP. No business logic, no
  queries.
- **services/** — business logic and orchestration. Owns transaction boundaries
  (via the request-scoped session). Raises domain errors, never `HTTPException`.
- **repositories/** — the only code that issues database queries. No business
  rules.
- **models/** — SQLAlchemy ORM entities.
- **schemas/** — Pydantic v2 models forming the API's public contract.
- **integrations/** — all external I/O (HTTP, browsers, AI providers) behind
  interfaces so implementations are swappable and business logic stays testable.

## Consequences

- Business logic is unit-testable without a web server or real network.
- New subsystems follow the same shape, keeping the codebase legible as it grows.
- A small amount of boilerplate (mapping between ORM and Pydantic) is accepted as
  the cost of decoupling.

## Alternatives considered

- **Fat routers / "FastAPI CRUD" style** — faster initially but couples transport
  to persistence; rejected given the target scale.
- **Full hexagonal/ports-and-adapters with separate domain entities** — more
  isolation than needed today; the repository + service split captures most of the
  benefit at lower cost.
