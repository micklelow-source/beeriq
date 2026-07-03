"""Structured extraction schemas (spec §3).

These are the validated target shapes the AI extraction layer produces from
arbitrary brewery HTML. ``extra="forbid"`` makes the generated JSON schema
``additionalProperties: false``, which the structured-outputs API requires.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BeerExtraction(BaseModel):
    """A single beer parsed from a tap or beer page."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="The beer's name.")
    style: str | None = Field(default=None, description="Beer style, e.g. 'Hazy IPA'.")
    abv: float | None = Field(default=None, description="Alcohol by volume as a percentage.")
    ibu: float | None = Field(default=None, description="International Bitterness Units.")
    availability: str | None = Field(
        default=None,
        description="Availability note, e.g. 'on tap', 'coming soon', 'sold out'.",
    )
    description: str | None = Field(default=None, description="Tasting notes / description.")
    seasonal: bool = Field(default=False, description="True if described as seasonal.")
    limited: bool = Field(default=False, description="True if described as limited release.")


class FoodTruckExtraction(BaseModel):
    """A food-truck appearance parsed from the site."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Food truck / vendor name.")
    schedule: str | None = Field(default=None, description="When they'll be present, if stated.")


class EventExtraction(BaseModel):
    """An event parsed from an events/calendar page."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Event title.")
    date: str | None = Field(default=None, description="Event date/time as written on the page.")
    description: str | None = Field(default=None, description="Event description, if any.")


class TapListExtraction(BaseModel):
    """The full structured result extracted from a brewery page.

    Every field defaults to empty so a page with no relevant content yields a
    valid, empty result rather than an error.
    """

    model_config = ConfigDict(extra="forbid")

    beers: list[BeerExtraction] = Field(default_factory=list)
    food_trucks: list[FoodTruckExtraction] = Field(default_factory=list)
    events: list[EventExtraction] = Field(default_factory=list)
    hours: str | None = Field(default=None, description="Opening hours as written, if present.")
    amenities: list[str] = Field(
        default_factory=list,
        description="Amenities, e.g. 'dog friendly', 'outdoor seating', 'food'.",
    )
