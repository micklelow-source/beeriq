# Developer onboarding

Welcome to BrewIQ. This gets you productive in ~15 minutes.

## 1. Read these first

1. [`docs/implementation/PHASE_6_MASTER_SPEC.md`](implementation/PHASE_6_MASTER_SPEC.md) — the canonical scope.
2. [`docs/architecture/`](architecture/) — the ADRs, especially ADR-0001 (layering).

## 2. Backend setup (no Docker required)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                               # full suite runs on SQLite; no services needed
```

Run the API:

```bash
uvicorn app.main:app --reload
```

- Interactive docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## 3. Full stack with Docker

```bash
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeds.nh_breweries
```

## 4. Where code goes (see ADR-0001)

| You want to… | Put it in… |
|---|---|
| Add an endpoint | `app/api/v1/` (transport only) |
| Add business logic | `app/services/` |
| Add a query | `app/repositories/` |
| Add a table | `app/models/` + an Alembic migration |
| Add a request/response shape | `app/schemas/` |
| Wrap an external system (HTTP, browser, AI) | `app/integrations/` behind an interface |

Rules of thumb: routers never query the database; services never build HTTP
responses; repositories never hold business rules; every external call sits behind
an interface so it can be faked in tests.

## 5. Testing conventions

- Unit tests inject fakes (e.g. `FakeFetcher` in `tests/conftest.py`) — no network.
- Integration tests drive the ASGI app via httpx `AsyncClient`.
- Target: 90% backend coverage. Run `pytest --cov=app --cov-report=term-missing`.

## 6. Before you push

```bash
ruff check .            # lint
mypy app                # type-check
pytest --cov=app        # tests + coverage
```

CI (GitHub Actions) runs the same checks on every PR.

## 7. Migrations

```bash
alembic revision --autogenerate -m "add X"   # generate
alembic upgrade head                          # apply
alembic downgrade -1                          # roll back one
```
