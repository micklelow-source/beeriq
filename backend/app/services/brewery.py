"""Brewery service — business logic around brewery records."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.core.utils import slugify
from app.models.brewery import Brewery
from app.repositories.brewery import BreweryRepository
from app.schemas.brewery import BreweryCreate


class BreweryService:
    """Create and query breweries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BreweryRepository(session)

    async def create(self, payload: BreweryCreate) -> Brewery:
        """Create a brewery, deriving a unique slug when none is supplied.

        Raises :class:`ConflictError` if the resulting slug already exists.
        """

        slug = payload.slug or slugify(payload.name)
        if await self.repo.get_by_slug(slug) is not None:
            raise ConflictError(f"Brewery with slug {slug!r} already exists")

        brewery = Brewery(
            name=payload.name,
            slug=slug,
            website=str(payload.website) if payload.website else None,
            brewery_type=payload.brewery_type,
            city=payload.city,
            state=payload.state.upper() if payload.state else None,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        return await self.repo.add(brewery)

    async def get(self, brewery_id: uuid.UUID) -> Brewery:
        brewery = await self.repo.get(brewery_id)
        if brewery is None:
            raise NotFoundError(f"Brewery {brewery_id} not found")
        return brewery

    async def list(
        self,
        *,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Brewery], int]:
        """Return a page of breweries and the total count."""

        if state:
            items = await self.repo.list_by_state(state, limit=limit, offset=offset)
        else:
            items = await self.repo.list(limit=limit, offset=offset)
        total = await self.repo.count()
        return items, total

    async def upsert_by_slug(self, payload: BreweryCreate) -> tuple[Brewery, bool]:
        """Idempotent upsert by slug (used by the seed importer).

        Returns ``(brewery, created)`` -- ``created`` is True only when this
        call inserted a brand-new row, letting callers (e.g. a directory
        refresh) find just the breweries that are new since the last import
        without a separate diffing pass.

        For an existing brewery, backfills only fields that are currently
        empty -- it never overwrites data already on the record. Directory
        re-imports are common (new Open Brewery DB snapshots, re-running for
        a state), and fields like ``website`` are also where manual
        corrections live (e.g. fixing a hijacked or dead domain); silently
        overwriting those with a stale upstream value on every re-import
        would undo that work.
        """

        slug = payload.slug or slugify(payload.name)
        existing = await self.repo.get_by_slug(slug)
        if existing is not None:
            if existing.website is None and payload.website:
                existing.website = str(payload.website)
            if existing.brewery_type is None and payload.brewery_type:
                existing.brewery_type = payload.brewery_type
            if existing.city is None and payload.city:
                existing.city = payload.city
            if existing.state is None and payload.state:
                existing.state = payload.state.upper()
            if existing.latitude is None and payload.latitude is not None:
                existing.latitude = payload.latitude
            if existing.longitude is None and payload.longitude is not None:
                existing.longitude = payload.longitude
            await self.session.flush()
            return existing, False
        try:
            return await self.create(payload), True
        except ConflictError:  # pragma: no cover - race guard
            refreshed = await self.repo.get_by_slug(slug)
            assert refreshed is not None
            return refreshed, False
