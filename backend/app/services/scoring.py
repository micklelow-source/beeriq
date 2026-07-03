"""BrewIQ Score v2 (spec §5).

The scoring math is a pure function of a :class:`ScoringInputs` snapshot, so it
is exhaustively unit-testable without a database. :class:`ScoringService`
gathers those inputs from the repositories and persists each result.

Each component yields a 0–100 value and an ``available`` flag. The overall score
is the weight-renormalized average of the *available* components, so a brewery is
never penalized for signals we simply don't have yet — instead that shows up as a
lower ``data_confidence`` (the share of intended signal actually backed by data).
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.models.brewery_score import BreweryScore
from app.models.change_event import ChangeEventType
from app.models.discovered_url import PageType
from app.repositories.brewery import BreweryRepository
from app.repositories.brewery_score import BreweryScoreRepository
from app.repositories.change_event import ChangeEventRepository
from app.repositories.discovered_url import DiscoveredURLRepository
from app.repositories.extraction import ExtractionRepository
from app.schemas.extraction import BeerExtraction, EventExtraction, TapListExtraction

logger = get_logger(__name__)

# Component weights (quality signals only). data_confidence is reported
# separately rather than averaged into the overall.
WEIGHTS: dict[str, float] = {
    "freshness": 0.25,
    "tap_rotation": 0.20,
    "beer_diversity": 0.15,
    "website_quality": 0.15,
    "event_activity": 0.10,
    "historical_reliability": 0.10,
    "social_activity": 0.05,
}

_MEANINGFUL_PAGE_TYPES = {
    PageType.TAP,
    PageType.BEER,
    PageType.MENU,
    PageType.EVENTS,
    PageType.FOOD_TRUCK,
}
_FRESHNESS_HORIZON_DAYS = 30.0
_ROTATION_WINDOW_DAYS = 30


@dataclass(frozen=True, slots=True)
class ScoringInputs:
    """Everything the pure scorer needs, gathered from the repositories."""

    now: datetime
    latest_extraction_at: datetime | None
    extraction_count: int
    beers: list[BeerExtraction]
    events: list[EventExtraction]
    discovered_page_types: set[PageType]
    has_events_page: bool
    rotation_changes_recent: int


@dataclass(frozen=True, slots=True)
class ComponentScore:
    name: str
    value: float | None
    available: bool
    weight: float


@dataclass(frozen=True, slots=True)
class ScoreResult:
    overall: float
    data_confidence: float
    components: list[ComponentScore]
    recommendations: list[str] = field(default_factory=list)
    trend_direction: str = "new"
    trend_delta: float | None = None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _aware(dt: datetime) -> datetime:
    """Treat naive timestamps (SQLite) as UTC so arithmetic is consistent."""

    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _freshness(inputs: ScoringInputs) -> tuple[float | None, bool]:
    if inputs.latest_extraction_at is None:
        return None, False
    age_days = (_aware(inputs.now) - _aware(inputs.latest_extraction_at)).total_seconds() / 86400
    return _clamp(100.0 - (age_days / _FRESHNESS_HORIZON_DAYS) * 100.0), True


def _tap_rotation(inputs: ScoringInputs) -> tuple[float | None, bool]:
    # Rotation needs at least two extractions to have anything to compare.
    if inputs.extraction_count < 2:
        return None, False
    c = inputs.rotation_changes_recent
    if c == 0:
        return 20.0, True
    if c <= 2:
        return 50.0, True
    if c <= 5:
        return 75.0, True
    return 100.0, True


def _beer_diversity(inputs: ScoringInputs) -> tuple[float | None, bool]:
    if not inputs.beers:
        return None, False
    styles = {b.style.strip().lower() for b in inputs.beers if b.style}
    return min(len(styles) / 8.0, 1.0) * 100.0, True


def _event_activity(inputs: ScoringInputs) -> tuple[float | None, bool]:
    if not inputs.has_events_page and not inputs.events:
        return None, False
    return min(len(inputs.events) / 3.0, 1.0) * 100.0, True


def _website_quality(inputs: ScoringInputs) -> tuple[float | None, bool]:
    if not inputs.discovered_page_types:
        return None, False
    present = len(inputs.discovered_page_types & _MEANINGFUL_PAGE_TYPES)
    return present / len(_MEANINGFUL_PAGE_TYPES) * 100.0, True


def _historical_reliability(inputs: ScoringInputs) -> tuple[float | None, bool]:
    if inputs.extraction_count == 0:
        return None, False
    return min(inputs.extraction_count / 10.0, 1.0) * 100.0, True


def _social_activity(inputs: ScoringInputs) -> tuple[float | None, bool]:
    # No social integration yet (spec §5); reported as an unavailable signal
    # rather than a fabricated number.
    return None, False


_COMPONENTS = {
    "freshness": _freshness,
    "tap_rotation": _tap_rotation,
    "beer_diversity": _beer_diversity,
    "website_quality": _website_quality,
    "event_activity": _event_activity,
    "historical_reliability": _historical_reliability,
    "social_activity": _social_activity,
}


def _recommendations(inputs: ScoringInputs, components: dict[str, ComponentScore]) -> list[str]:
    recs: list[str] = []
    if PageType.TAP not in inputs.discovered_page_types:
        recs.append("No tap page discovered — run discovery to track live beers.")
    freshness = components["freshness"]
    if freshness.available and freshness.value is not None and freshness.value < 50:
        recs.append("Tap data is getting stale — re-scrape this brewery soon.")
    if not components["beer_diversity"].available:
        recs.append("No beers extracted yet — scrape and extract a tap or beer page.")
    diversity = components["beer_diversity"]
    if diversity.available and diversity.value is not None and diversity.value < 40:
        recs.append("Low style diversity detected on the current tap list.")
    website = components["website_quality"]
    if website.available and website.value is not None and website.value < 60:
        recs.append("Few brewery page types discovered — coverage looks incomplete.")
    if not components["social_activity"].available:
        recs.append("Connect a social feed to score social activity (not yet integrated).")
    return recs


def _trend(overall: float, previous_overall: float | None) -> tuple[str, float | None]:
    if previous_overall is None:
        return "new", None
    delta = round(overall - previous_overall, 1)
    if delta > 1.0:
        return "up", delta
    if delta < -1.0:
        return "down", delta
    return "flat", delta


def compute_score(
    inputs: ScoringInputs, *, previous_overall: float | None = None
) -> ScoreResult:
    """Compute a :class:`ScoreResult` from a snapshot of a brewery's data."""

    components: dict[str, ComponentScore] = {}
    for name, fn in _COMPONENTS.items():
        value, available = fn(inputs)
        components[name] = ComponentScore(
            name=name,
            value=round(value, 1) if value is not None else None,
            available=available,
            weight=WEIGHTS[name],
        )

    available_weight = sum(c.weight for c in components.values() if c.available)
    total_weight = sum(WEIGHTS.values())
    if available_weight > 0:
        overall = sum(
            c.weight * (c.value or 0.0) for c in components.values() if c.available
        ) / available_weight
    else:
        overall = 0.0

    data_confidence = round(available_weight / total_weight, 2)
    ordered = [components[name] for name in WEIGHTS]
    direction, delta = _trend(round(overall, 1), previous_overall)

    return ScoreResult(
        overall=round(overall, 1),
        data_confidence=data_confidence,
        components=ordered,
        recommendations=_recommendations(inputs, components),
        trend_direction=direction,
        trend_delta=delta,
    )


def rotation_window_start(now: datetime) -> datetime:
    """Naive-UTC lower bound for the rotation window (SQLite-comparison safe)."""

    start = _aware(now) - timedelta(days=_ROTATION_WINDOW_DAYS)
    return start.replace(tzinfo=None)


ROTATION_EVENT_TYPES = (ChangeEventType.BEER_ADDED, ChangeEventType.BEER_REMOVED)


def _dedup_beers(beers: list[BeerExtraction]) -> list[BeerExtraction]:
    seen: dict[str, BeerExtraction] = {}
    for beer in beers:
        seen.setdefault(beer.name.strip().lower(), beer)
    return list(seen.values())


def _dedup_events(events: list[EventExtraction]) -> list[EventExtraction]:
    seen: dict[str, EventExtraction] = {}
    for event in events:
        seen.setdefault(event.title.strip().lower(), event)
    return list(seen.values())


class ScoringService:
    """Gathers a brewery's data, computes a score, and persists it."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.breweries = BreweryRepository(session)
        self.urls = DiscoveredURLRepository(session)
        self.extractions = ExtractionRepository(session)
        self.events = ChangeEventRepository(session)
        self.scores = BreweryScoreRepository(session)

    async def _gather_inputs(self, brewery_id: uuid.UUID) -> ScoringInputs:
        now = datetime.now(UTC)
        urls = await self.urls.list_for_brewery(brewery_id)
        page_types = {u.page_type for u in urls}

        beers: list[BeerExtraction] = []
        events: list[EventExtraction] = []
        latest_at: datetime | None = None
        for url in urls:
            extraction = await self.extractions.latest_for_url(url.id)
            if extraction is None:
                continue
            data = TapListExtraction.model_validate(extraction.payload)
            beers.extend(data.beers)
            events.extend(data.events)
            if latest_at is None or extraction.created_at > latest_at:
                latest_at = extraction.created_at

        rotation = await self.events.count_recent_by_type(
            brewery_id, ROTATION_EVENT_TYPES, rotation_window_start(now)
        )
        return ScoringInputs(
            now=now,
            latest_extraction_at=latest_at,
            extraction_count=await self.extractions.count_for_brewery(brewery_id),
            beers=_dedup_beers(beers),
            events=_dedup_events(events),
            discovered_page_types=page_types,
            has_events_page=PageType.EVENTS in page_types,
            rotation_changes_recent=rotation,
        )

    async def compute_and_store(self, brewery_id: uuid.UUID) -> BreweryScore:
        """Compute the brewery's score, persist it, and return the stored row.

        Raises :class:`NotFoundError` if the brewery does not exist.
        """

        if await self.breweries.get(brewery_id) is None:
            raise NotFoundError(f"Brewery {brewery_id} not found")

        inputs = await self._gather_inputs(brewery_id)
        previous = await self.scores.latest_for_brewery(brewery_id)
        result = compute_score(
            inputs, previous_overall=previous.overall if previous else None
        )

        row = await self.scores.add(
            BreweryScore(
                brewery_id=brewery_id,
                overall=result.overall,
                data_confidence=result.data_confidence,
                components=[asdict(c) for c in result.components],
                recommendations=result.recommendations,
                trend_direction=result.trend_direction,
                trend_delta=result.trend_delta,
            )
        )
        logger.info(
            "Computed BrewIQ score",
            extra={
                "brewery": str(brewery_id),
                "overall": result.overall,
                "confidence": result.data_confidence,
            },
        )
        return row
