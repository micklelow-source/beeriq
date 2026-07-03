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

    async def upsert_by_slug(self, payload: BreweryCreate) -> Brewery:
        """Idempotent create-or-return by slug (used by the seed importer)."""

        slug = payload.slug or slugify(payload.name)
        existing = await self.repo.get_by_slug(slug)
        if existing is not None:
            return existing
        try:
            return await self.create(payload)
        except ConflictError:  # pragma: no cover - race guard
            refreshed = await self.repo.get_by_slug(slug)
            assert refreshed is not None
            return refreshed
