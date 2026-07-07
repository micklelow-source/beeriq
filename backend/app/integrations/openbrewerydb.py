"""Open Brewery DB client.

Open Brewery DB (https://www.openbrewerydb.org) is a free, public **directory** of
breweries — names, addresses, websites, and coordinates. It does NOT provide tap
lists, events, or food trucks; those come from the scrape + AI-extraction pipeline
(spec §1–3). This client is used to seed/expand the brewery directory.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_BASE_URL = "https://api.openbrewerydb.org/v1"
# Brewery types that aren't operating taprooms worth tracking.
_EXCLUDED_TYPES = {"closed", "planning"}


@dataclass(frozen=True, slots=True)
class DirectoryBrewery:
    """A brewery record from the Open Brewery DB directory."""

    name: str
    brewery_type: str | None
    website: str | None
    city: str | None
    state_code: str
    latitude: float | None
    longitude: float | None


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class OpenBreweryDBClient:
    """Fetches brewery directory records from Open Brewery DB."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=self._settings.http_timeout_seconds,
            headers={"User-Agent": self._settings.http_user_agent, "Accept": "application/json"},
        )

    async def breweries_by_state(
        self, state_slug: str, state_code: str, *, include_excluded: bool = False
    ) -> list[DirectoryBrewery]:
        """Return all directory breweries for a state (paginated).

        ``state_slug`` is the Open Brewery DB form (e.g. ``"new_hampshire"``);
        ``state_code`` is the 2-letter USPS code stored on our records.
        """

        results: list[DirectoryBrewery] = []
        page = 1
        while True:
            response = await self._client.get(
                "/breweries",
                params={"by_state": state_slug, "per_page": 200, "page": page},
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            for record in batch:
                brewery_type = record.get("brewery_type")
                if not include_excluded and brewery_type in _EXCLUDED_TYPES:
                    continue
                results.append(
                    DirectoryBrewery(
                        name=record["name"],
                        brewery_type=brewery_type,
                        website=record.get("website_url") or None,
                        city=record.get("city"),
                        state_code=state_code,
                        latitude=_to_float(record.get("latitude")),
                        longitude=_to_float(record.get("longitude")),
                    )
                )
            if len(batch) < 200:
                break
            page += 1

        logger.info(
            "Fetched Open Brewery DB directory",
            extra={"state": state_code, "count": len(results)},
        )
        return results

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OpenBreweryDBClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
