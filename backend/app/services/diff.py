"""Diff engine (spec §4).

``diff_extractions`` is a pure function comparing two extractions and returning
change drafts; :class:`DiffService` persists each extraction (history) and the
resulting change events. Keeping the comparison pure makes it exhaustively
unit-testable without a database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.change_event import ChangeEvent, ChangeEventType
from app.models.discovered_url import DiscoveredURL
from app.models.extraction import Extraction
from app.repositories.change_event import ChangeEventRepository
from app.repositories.extraction import ExtractionRepository
from app.schemas.extraction import TapListExtraction

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ChangeEventDraft:
    """A detected change, before it is attached to a brewery/URL and persisted."""

    event_type: ChangeEventType
    summary: str
    details: dict[str, Any]


def _norm(name: str) -> str:
    return name.strip().lower()


def diff_extractions(
    previous: TapListExtraction, latest: TapListExtraction
) -> list[ChangeEventDraft]:
    """Return the ordered set of changes from ``previous`` to ``latest``.

    Beers, events, and food trucks are matched case-insensitively by name/title.
    Output is sorted deterministically so callers (and tests) don't depend on
    dict iteration order.
    """

    drafts: list[ChangeEventDraft] = []

    prev_beers = {_norm(b.name): b for b in previous.beers}
    latest_beers = {_norm(b.name): b for b in latest.beers}

    for key, beer in latest_beers.items():
        if key not in prev_beers:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.BEER_ADDED,
                    f"New beer: {beer.name}",
                    {"name": beer.name, "style": beer.style, "abv": beer.abv},
                )
            )
    for key, beer in prev_beers.items():
        if key not in latest_beers:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.BEER_REMOVED,
                    f"Beer removed: {beer.name}",
                    {"name": beer.name},
                )
            )
    for key in prev_beers.keys() & latest_beers.keys():
        old, new = prev_beers[key], latest_beers[key]
        if old.abv != new.abv:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.BEER_ABV_CHANGED,
                    f"{new.name} ABV changed from {old.abv} to {new.abv}",
                    {"name": new.name, "old_abv": old.abv, "new_abv": new.abv},
                )
            )
        if (old.description or "") != (new.description or ""):
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.BEER_DESCRIPTION_CHANGED,
                    f"{new.name} description updated",
                    {"name": new.name},
                )
            )

    prev_events = {_norm(e.title): e for e in previous.events}
    latest_events = {_norm(e.title): e for e in latest.events}
    for key, event in latest_events.items():
        if key not in prev_events:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.EVENT_ADDED,
                    f"New event: {event.title}",
                    {"title": event.title, "date": event.date},
                )
            )
    for key, event in prev_events.items():
        if key not in latest_events:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.EVENT_REMOVED,
                    f"Event removed: {event.title}",
                    {"title": event.title},
                )
            )

    prev_trucks = {_norm(f.name): f for f in previous.food_trucks}
    latest_trucks = {_norm(f.name): f for f in latest.food_trucks}
    for key, truck in latest_trucks.items():
        if key not in prev_trucks:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.FOOD_TRUCK_ADDED,
                    f"Food truck announced: {truck.name}",
                    {"name": truck.name, "schedule": truck.schedule},
                )
            )
    for key, truck in prev_trucks.items():
        if key not in latest_trucks:
            drafts.append(
                ChangeEventDraft(
                    ChangeEventType.FOOD_TRUCK_REMOVED,
                    f"Food truck no longer listed: {truck.name}",
                    {"name": truck.name},
                )
            )

    if (previous.hours or "") != (latest.hours or ""):
        drafts.append(
            ChangeEventDraft(
                ChangeEventType.HOURS_CHANGED,
                "Hours changed",
                {"old": previous.hours, "new": latest.hours},
            )
        )

    drafts.sort(key=lambda d: (d.event_type.value, d.summary))
    return drafts


class DiffService:
    """Persists extractions and the change events derived from them."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.extractions = ExtractionRepository(session)
        self.events = ChangeEventRepository(session)

    async def record(
        self, discovered: DiscoveredURL, latest: TapListExtraction
    ) -> list[ChangeEvent]:
        """Store ``latest`` and return the change events vs. the prior extraction.

        The first extraction for a URL establishes a baseline and yields no
        events. The new extraction is always persisted for history.
        """

        previous_row = await self.extractions.latest_for_url(discovered.id)
        await self.extractions.add(
            Extraction(
                discovered_url_id=discovered.id,
                payload=latest.model_dump(mode="json"),
            )
        )

        if previous_row is None:
            logger.info("Baseline extraction stored", extra={"url": discovered.url})
            return []

        previous = TapListExtraction.model_validate(previous_row.payload)
        drafts = diff_extractions(previous, latest)

        events: list[ChangeEvent] = []
        for draft in drafts:
            events.append(
                await self.events.add(
                    ChangeEvent(
                        brewery_id=discovered.brewery_id,
                        discovered_url_id=discovered.id,
                        event_type=draft.event_type,
                        summary=draft.summary,
                        details=draft.details,
                    )
                )
            )
        logger.info(
            "Recorded change events",
            extra={"url": discovered.url, "count": len(events)},
        )
        return events
