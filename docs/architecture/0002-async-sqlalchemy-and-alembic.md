# ADR-0002: Async SQLAlchemy 2.x + Alembic

- Status: Accepted
- Date: 2026-07-02

## Context

The platform is I/O-bound: it fans out to many brewery sites, AI providers, and
search/notification backends concurrently. FastAPI is async-first. We need an ORM
and migration story that fit that model and support PostgreSQL 16 + PostGIS in
production while keeping the test suite fast and dependency-free.

## Decision

- Use **SQLAlchemy 2.x** with the async engine (`asyncpg` in production).
- Use the modern typed `Mapped[...]` / `mapped_column` declarative style.
- Use **Alembic** for migrations, with the environment reading the database URL
  from application settings (single source of truth).
- Use a **portable `Uuid` primary key** that maps to native `uuid` on PostgreSQL
  and to a 32-char string on SQLite, so the same models run against an in-memory
  SQLite database in tests (no Postgres/Redis needed for CI unit tests).
- Avoid PostGIS-specific column types in shared models until the route planner
  (spec §7) needs them; introduce them via a dedicated migration then.

## Consequences

- Tests run in seconds against SQLite with the identical ORM models.
- Transaction boundaries live in the service layer / request dependency
  (`session_scope` / `get_session`), keeping repositories side-effect-light.
- Some Postgres-only features (PostGIS, full-text) require integration tests
  against a real Postgres; those are marked separately from unit tests.

## Alternatives considered

- **Sync SQLAlchemy + threadpool** — simpler but wastes the async stack under load.
- **Tortoise ORM / SQLModel** — less mature migration/tooling story for our scale.
