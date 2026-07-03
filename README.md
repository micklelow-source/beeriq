# BrewIQ

BrewIQ is a data platform that discovers brewery websites, extracts live tap lists
and menus, tracks how they change over time, and scores each brewery on freshness,
rotation, diversity, and activity. It starts with New Hampshire breweries and is
architected to scale nationwide without structural rework.

This repository is a greenfield build following the canonical specification in
[`docs/implementation/PHASE_6_MASTER_SPEC.md`](docs/implementation/PHASE_6_MASTER_SPEC.md).
Significant design decisions are recorded as ADRs under
[`docs/architecture/`](docs/architecture).

## Current status

The foundation and a working **vertical slice** are implemented:

- Clean-architecture FastAPI backend (models → repositories → services → API).
- Async SQLAlchemy 2.x + Alembic migrations, Pydantic v2 settings and schemas.
- Structured logging, typed config, dependency-injected sessions.
- **Website Discovery Engine** (probes common tap/beer/menu/events paths).
- **Fetcher abstraction** with an httpx implementation (Playwright crawler slotted
  behind the same interface — see [ADR-0003](docs/architecture/0003-fetcher-abstraction.md)).
- **Scrape + snapshot** pipeline with content hashing (change detection).
- Seed importer for real New Hampshire breweries.
- pytest suite covering discovery, repositories, scraping, and the REST API.
- Docker Compose (Postgres 16 + PostGIS, Redis) and a Next.js 15 frontend scaffold.

Later Phase 6 subsystems (AI extraction, diff/history, scoring v2, notifications,
route planner, WebSockets, OpenSearch, monitoring) are specified and have ADRs /
interface seams prepared, but are intentionally not yet implemented — see the spec.

## Architecture

```
backend/app/
  core/          config, logging, database engine/session
  models/        SQLAlchemy ORM entities
  schemas/       Pydantic v2 request/response models
  repositories/  data-access layer (no business logic)
  services/      business logic / orchestration
  integrations/  external I/O (HTTP fetcher, later Playwright/AI providers)
  api/v1/        FastAPI routers (transport only)
  seeds/         reference data importers
```

Dependencies flow inward: `api → services → repositories → models`. The API layer
never touches the database directly; services never build HTTP responses.

## Quick start (local, no Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                              # runs the full test suite (SQLite, no services needed)
uvicorn app.main:app --reload      # serves the API at http://localhost:8000
```

Open http://localhost:8000/docs for interactive API documentation.

## Quick start (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

This brings up Postgres+PostGIS, Redis, the API, and the frontend. Run migrations
and seed NH breweries:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeds.nh_breweries
```

## Documentation

- [Master specification](docs/implementation/PHASE_6_MASTER_SPEC.md)
- [Architecture decision records](docs/architecture/)
- [Developer onboarding](docs/onboarding.md)
