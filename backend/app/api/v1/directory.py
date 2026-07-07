"""Cross-brewery directory endpoints: events and food trucks (spec §8)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.schemas.directory import BreweryEvent, BreweryFoodTruck
from app.services.current import CurrentDataService

router = APIRouter(tags=["directory"])


@router.get(
    "/events",
    response_model=list[BreweryEvent],
    summary="Current events across all breweries",
)
async def list_events(session: AsyncSession = SessionDep) -> list[BreweryEvent]:
    pairs = await CurrentDataService(session).all_events()
    return [
        BreweryEvent(
            brewery_id=brewery.id,
            brewery_name=brewery.name,
            brewery_slug=brewery.slug,
            brewery_state=brewery.state,
            title=event.title,
            date=event.date,
            description=event.description,
        )
        for brewery, event in pairs
    ]


@router.get(
    "/food-trucks",
    response_model=list[BreweryFoodTruck],
    summary="Current food trucks across all breweries",
)
async def list_food_trucks(
    session: AsyncSession = SessionDep,
) -> list[BreweryFoodTruck]:
    pairs = await CurrentDataService(session).all_food_trucks()
    return [
        BreweryFoodTruck(
            brewery_id=brewery.id,
            brewery_name=brewery.name,
            brewery_slug=brewery.slug,
            brewery_state=brewery.state,
            name=truck.name,
            schedule=truck.schedule,
        )
        for brewery, truck in pairs
    ]
