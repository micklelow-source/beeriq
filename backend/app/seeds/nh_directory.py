"""Import the full New Hampshire brewery directory from Open Brewery DB.

    python -m app.seeds.nh_directory

Idempotent (upsert by slug). Records with an invalid website URL are imported
without a website rather than skipped, so directory coverage stays complete.
"""

from __future__ import annotations

import asyncio

from pydantic import ValidationError

from app.core.database import session_scope
from app.core.logging import get_logger
from app.integrations.openbrewerydb import DirectoryBrewery, OpenBreweryDBClient
from app.schemas.brewery import BreweryCreate
from app.services.brewery import BreweryService

logger = get_logger(__name__)


def _to_payload(record: DirectoryBrewery, *, drop_website: bool = False) -> BreweryCreate:
    return BreweryCreate(
        name=record.name,
        website=None if drop_website else record.website,
        city=record.city,
        state=record.state_code,
        latitude=record.latitude,
        longitude=record.longitude,
    )


async def import_nh_directory() -> int:
    """Fetch and upsert all active NH breweries. Returns the number imported."""

    async with OpenBreweryDBClient() as client:
        records = await client.breweries_by_state("new_hampshire", "NH")

    imported = 0
    async with session_scope() as session:
        service = BreweryService(session)
        for record in records:
            try:
                payload = _to_payload(record)
            except ValidationError:
                # Almost always a malformed website_url — import without it.
                payload = _to_payload(record, drop_website=True)
            await service.upsert_by_slug(payload)
            imported += 1

    logger.info("NH directory import complete", extra={"imported": imported})
    return imported


def main() -> None:
    count = asyncio.run(import_nh_directory())
    logger.info("Imported %d NH breweries from Open Brewery DB", count)


if __name__ == "__main__":
    main()
