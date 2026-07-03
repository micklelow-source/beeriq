"""Live activity feed (spec §8).

Builds a cross-brewery, reverse-chronological feed from two sources — change
events (new/removed beers, events, food trucks, hours) and BrewIQ score
increases — using a SQL ``UNION ALL`` so pagination is correct and cheap even as
the feed grows. Only the requested page is hydrated into full items.
"""

from __future__ import annotations

from sqlalchemy import func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brewery import Brewery
from app.models.brewery_score import BreweryScore
from app.models.change_event import ChangeEvent
from app.schemas.feed import FeedItem


class FeedService:
    """Assembles the paginated activity feed."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _union(self):
        change_events = select(
            ChangeEvent.id.label("item_id"),
            literal("change_event").label("kind"),
            ChangeEvent.brewery_id.label("brewery_id"),
            ChangeEvent.created_at.label("created_at"),
        )
        score_increases = select(
            BreweryScore.id,
            literal("score_increase"),
            BreweryScore.brewery_id,
            BreweryScore.created_at,
        ).where(BreweryScore.trend_direction == "up")
        return change_events.union_all(score_increases).subquery()

    async def page(self, *, limit: int, offset: int) -> tuple[list[FeedItem], int]:
        union = self._union()
        total = await self.session.scalar(
            select(func.count()).select_from(union)
        )
        rows = (
            await self.session.execute(
                select(
                    union.c.item_id, union.c.kind, union.c.brewery_id, union.c.created_at
                )
                .order_by(union.c.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()

        if not rows:
            return [], int(total or 0)

        change_ids = [r.item_id for r in rows if r.kind == "change_event"]
        score_ids = [r.item_id for r in rows if r.kind == "score_increase"]
        brewery_ids = {r.brewery_id for r in rows}

        changes = await self._by_id(ChangeEvent, change_ids)
        scores = await self._by_id(BreweryScore, score_ids)
        breweries = await self._by_id(Brewery, list(brewery_ids))

        items: list[FeedItem] = []
        for row in rows:  # already sorted newest-first by the union query
            brewery = breweries[row.brewery_id]
            if row.kind == "change_event":
                event = changes[row.item_id]
                summary = event.summary
                # Surface the event type so clients can badge each item correctly.
                details = {**event.details, "event_type": event.event_type.value}
            else:
                score = scores[row.item_id]
                delta = f"+{score.trend_delta}" if score.trend_delta is not None else ""
                summary = f"BrewIQ score rose to {score.overall} ({delta})"
                details = {"overall": score.overall, "delta": score.trend_delta}
            items.append(
                FeedItem(
                    id=row.item_id,
                    kind=row.kind,
                    brewery_id=row.brewery_id,
                    brewery_name=brewery.name,
                    brewery_slug=brewery.slug,
                    summary=summary,
                    details=details,
                    created_at=row.created_at,
                )
            )
        return items, int(total or 0)

    async def _by_id(self, model, ids):
        """Return a ``{id: row}`` map for the given ids (empty if none)."""

        if not ids:
            return {}
        result = await self.session.scalars(select(model).where(model.id.in_(ids)))
        return {row.id: row for row in result}
