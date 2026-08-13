"""Curated beer-festival / tasting-event seed, sourced from beerfests.com.

Unlike the tap-list/food-truck/event scrapers (which extract data *from a
brewery's own website*), festivals are standalone calendar entries -- most
aren't hosted by a single brewery already in the BrewIQ directory -- so this
data is manually curated from beerfests.com's homepage and per-state listing
pages rather than scraped/AI-extracted. Re-run freely: upserts by a slug
derived from ``name`` + ``event_date.year``, so it's safe to run again after
adding more rows or when dates roll into the next year.

    python -m app.seeds.festivals

Data snapshot date: 2026-08-13. Coverage: CA, CO, CT, FL, IL, IN, MA, MD, ME,
MI, MN, NC, NH, NJ, NY, OK, OR, PA, RI, TN, TX, VA, VT, WA (no results found
for AZ, GA, KY, MO, NV, OH, SC, WI at snapshot time).
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import date

from app.core.database import session_scope
from app.core.logging import get_logger
from app.models.festival import Festival, FestivalCategory
from app.repositories.festival import FestivalRepository

logger = get_logger(__name__)

_FESTIVAL = FestivalCategory.FESTIVAL
_TASTING = FestivalCategory.TASTING

_STATE_LISTING_URL = {
    "CA": "https://beerfests.com/us/california-beer-festivals",
    "CO": "https://beerfests.com/us/colorado-beer-festivals",
    "FL": "https://beerfests.com/us/florida-beer-festivals",
    "IL": "https://beerfests.com/us/illinois-beer-festivals",
    "IN": "https://beerfests.com/us/indiana-beer-festivals",
    "MA": "https://beerfests.com/us/massachusetts-beer-festivals",
    "MD": "https://beerfests.com/us/maryland-beer-festivals",
    "ME": "https://beerfests.com/us/maine-beer-festivals",
    "MI": "https://beerfests.com/us/michigan-beer-festivals",
    "MN": "https://beerfests.com/us/minnesota-beer-festivals",
    "NC": "https://beerfests.com/us/north-carolina-beer-festivals",
    "NJ": "https://beerfests.com/us/new-jersey-beer-festivals",
    "NY": "https://beerfests.com/us/new-york-beer-festivals",
    "OR": "https://beerfests.com/us/oregon-beer-festivals",
    "PA": "https://beerfests.com/us/pennsylvania-beer-festivals",
    "TN": "https://beerfests.com/us/tennessee-beer-festivals",
    "TX": "https://beerfests.com/us/texas-beer-festivals",
    "VA": "https://beerfests.com/us/virginia-beer-festivals",
    "VT": "https://beerfests.com/us/vermont-beer-festivals",
    "WA": "https://beerfests.com/us/washington-beer-festivals",
}


@dataclass(frozen=True)
class _Row:
    name: str
    category: FestivalCategory
    event_date: date | None
    city: str | None
    state: str | None
    url: str
    description: str | None = None


# (name, category, date, city, state, url override or None for the state
# listing page, description). Dates/cities as published on beerfests.com;
# "Multi-day event" notes a "+ 1 more" marker on the listing (a second day
# whose exact date wasn't itemized).
_ROWS: list[_Row] = [
    _Row(
        "ShakesBeer Festival",
        _FESTIVAL,
        date(2026, 8, 15),
        "Stratford",
        "CT",
        "https://beerfests.com/events/shakesbeer-festival",
    ),
    _Row(
        "Spirit of Hudson Food & Brewfest",
        _FESTIVAL,
        date(2026, 8, 15),
        "Hudson",
        "MA",
        "https://beerfests.com/events/spirit-of-hudson-food-brewfest",
    ),
    _Row(
        "Lonely Roads Fest",
        _FESTIVAL,
        date(2026, 9, 5),
        "Stratford",
        "CT",
        "https://beerfests.com/events/lonely-roads-fest",
    ),
    _Row(
        "Raise the Barn",
        _FESTIVAL,
        date(2026, 9, 12),
        "Exeter",
        "RI",
        "https://beerfests.com/events/raise-the-barn",
    ),
    _Row(
        "Real Ale Beer Festival & Cask Challenge",
        _FESTIVAL,
        date(2026, 9, 12),
        "West Hartford",
        "CT",
        "https://beerfests.com/events/real-ale-harvest-festival",
        "Multi-day event.",
    ),
    _Row(
        "Brass City Brew Fest",
        _FESTIVAL,
        date(2026, 9, 12),
        "Waterbury",
        "CT",
        "https://beerfests.com/events/brass-city-brewfest",
    ),
    _Row(
        "Annual Bourbon & Beer Fest At The Vine Martini & Wine Bar",
        _FESTIVAL,
        date(2026, 9, 12),
        "Grayslake",
        "IL",
        "https://beerfests.com/events/the-vine-martini-wine-bar-annual-bourbon-beer-fest",
    ),
    _Row(
        "Brews, Brats, and Bands",
        _FESTIVAL,
        date(2026, 9, 12),
        "Canton",
        "MI",
        "https://beerfests.com/events/brew-brats-and-bands-at-the-barn",
    ),
    _Row(
        "Brewfest at the Beach",
        _FESTIVAL,
        date(2026, 9, 18),
        "New London",
        "CT",
        "https://beerfests.com/events/brewfest-at-the-beach",
    ),
    _Row(
        "Claremont Brewfest",
        _FESTIVAL,
        date(2026, 9, 19),
        "Claremont",
        "NH",
        "https://beerfests.com/events/claremont-brewfest",
    ),
    _Row(
        "Two Roads Ok2berfest 2026",
        _FESTIVAL,
        date(2026, 9, 19),
        "Stratford",
        "CT",
        "https://beerfests.com/events/two-roads-ok2berfest",
        "Multi-day event.",
    ),
    _Row(
        "Lagerfest @ Vulgar Brewing",
        _FESTIVAL,
        date(2026, 9, 19),
        "Franklin",
        "NH",
        "https://beerfests.com/events/vulgar-brewing-lager-fest",
    ),
    _Row(
        "Manchester Brewfest",
        _FESTIVAL,
        date(2026, 9, 19),
        "Manchester",
        "NH",
        "https://beerfests.com/events/manchester-brewfest",
    ),
    _Row(
        "Spacecat Brewing Company Oktoberfest",
        _FESTIVAL,
        date(2026, 9, 26),
        "Norwalk",
        "CT",
        "https://beerfests.com/events/spacecat-brewing-company-oktoberfest",
    ),
    _Row(
        "Schilling Beer Co. Oktoberfest 2026 & 13th Anniversary",
        _FESTIVAL,
        date(2026, 9, 26),
        "Littleton",
        "NH",
        "https://beerfests.com/events/schilling-okoberfest",
        "Multi-day event.",
    ),
    _Row(
        "Glassboro Craft Beer Festival",
        _FESTIVAL,
        date(2026, 9, 26),
        "Glassboro",
        "NJ",
        "https://beerfests.com/events/glassboro-craft-beer-festival",
    ),
    _Row(
        "Cadillac's Craft Beer Festival",
        _FESTIVAL,
        date(2026, 9, 26),
        "Cadillac",
        "MI",
        "https://beerfests.com/events/cadillac-craft-beer-festival",
    ),
    _Row(
        "McNellie's Harvest Beer Festival",
        _FESTIVAL,
        date(2026, 9, 26),
        "Tulsa",
        "OK",
        "https://beerfests.com/events/mcnellies-harvest-beer-festival",
    ),
    _Row(
        "Powder Keg Beer & Chili Festival",
        _FESTIVAL,
        date(2026, 10, 3),
        "Exeter",
        "NH",
        "https://beerfests.com/events/powder-keg-beer-and-chili-festival",
    ),
    _Row(
        "Friends of the West Invitational Beer Fest",
        _FESTIVAL,
        date(2026, 10, 3),
        "Grand Junction",
        "CO",
        "https://beerfests.com/events/friends-of-the-west-invitational-beer-fest",
    ),
    _Row(
        "Westoberfest",
        _FESTIVAL,
        date(2026, 10, 3),
        "Westport",
        "CT",
        "https://beerfests.com/events/westoberfest",
    ),
    _Row(
        "Mount Uncanoonuc Brewfest",
        _FESTIVAL,
        date(2026, 10, 17),
        "Goffstown",
        "NH",
        "https://beerfests.com/events/mount-uncanoonuc-brewfest",
    ),
    _Row(
        "Windermere Craft Beer Fest",
        _FESTIVAL,
        date(2026, 10, 17),
        "Windermere",
        "FL",
        "https://beerfests.com/events/windermere-craft-beer-fest",
    ),
    _Row(
        "Halloween in the Hangars Brew Fest",
        _FESTIVAL,
        date(2026, 10, 24),
        "Windsor Locks",
        "CT",
        "https://beerfests.com/events/halloween-in-the-hangars-brew-fest",
    ),
    _Row(
        "Great American Beer Festival",
        _FESTIVAL,
        date(2026, 10, 10),
        "Denver",
        "CO",
        "https://beerfests.com/events/great-american-beer-festival",
        "Multi-day event.",
    ),
    _Row(
        "Festival of Wood & Barrel-Aged Beer",
        _FESTIVAL,
        date(2026, 11, 13),
        "Chicago",
        "IL",
        "https://beerfests.com/events/festival-of-wood-barrel-aged-beer",
        "Multi-day event.",
    ),
    # California
    _Row(
        "Stumptown Beer Revival & BBQ Cook-Off",
        _FESTIVAL,
        date(2026, 8, 15),
        "Guerneville",
        "CA",
        _STATE_LISTING_URL["CA"],
    ),
    _Row(
        "Lake Arrowhead Brewfest",
        _FESTIVAL,
        date(2026, 8, 22),
        "Lake Arrowhead",
        "CA",
        _STATE_LISTING_URL["CA"],
    ),
    _Row(
        "Suds Francisco: A Funk & Fermentation Festival",
        _FESTIVAL,
        date(2026, 8, 23),
        "San Francisco",
        "CA",
        _STATE_LISTING_URL["CA"],
    ),
    _Row(
        "Rancho BEERnardo Festival",
        _FESTIVAL,
        date(2026, 10, 3),
        "San Diego",
        "CA",
        _STATE_LISTING_URL["CA"],
    ),
    _Row(
        "CCBA Summit Beer Festival",
        _FESTIVAL,
        date(2026, 11, 7),
        "Torrance",
        "CA",
        _STATE_LISTING_URL["CA"],
    ),
    # Texas
    _Row(
        "San Antonio Beer Festival",
        _FESTIVAL,
        date(2026, 10, 17),
        "San Antonio",
        "TX",
        _STATE_LISTING_URL["TX"],
    ),
    _Row(
        "Harker Heights Food, Wine & Brew Fest",
        _FESTIVAL,
        date(2026, 10, 17),
        "Harker Heights",
        "TX",
        _STATE_LISTING_URL["TX"],
    ),
    _Row(
        "Texas Craft Brewers Festival",
        _FESTIVAL,
        date(2026, 11, 14),
        "Austin",
        "TX",
        _STATE_LISTING_URL["TX"],
    ),
    # New York
    _Row(
        "Flour City Brewers' Festival",
        _FESTIVAL,
        date(2026, 8, 21),
        "Rochester",
        "NY",
        _STATE_LISTING_URL["NY"],
    ),
    # Washington
    _Row(
        "Pybus Market Fresh Hop Festival",
        _FESTIVAL,
        date(2026, 9, 26),
        "Wenatchee",
        "WA",
        _STATE_LISTING_URL["WA"],
    ),
    # Oregon
    _Row(
        "Little Woody Beer, Cider & Whiskey Festival",
        _FESTIVAL,
        date(2026, 8, 29),
        "Bend",
        "OR",
        _STATE_LISTING_URL["OR"],
    ),
    # Pennsylvania
    _Row(
        "Lancaster Craft Beerfest",
        _FESTIVAL,
        date(2026, 8, 22),
        "Lancaster",
        "PA",
        _STATE_LISTING_URL["PA"],
        "Multi-day event.",
    ),
    _Row(
        "Fonthill Castle Beer Fest",
        _FESTIVAL,
        date(2026, 8, 22),
        "Doylestown",
        "PA",
        _STATE_LISTING_URL["PA"],
    ),
    _Row(
        "Lititz Craft Beer Fest",
        _FESTIVAL,
        date(2026, 9, 26),
        "Lititz",
        "PA",
        _STATE_LISTING_URL["PA"],
    ),
    # North Carolina
    _Row(
        "High Country Beer Fest",
        _FESTIVAL,
        date(2026, 8, 29),
        "Boone",
        "NC",
        _STATE_LISTING_URL["NC"],
    ),
    # Colorado (additional, beyond the ones with direct event pages above)
    _Row(
        "Mt. Crested Butte Chili & Beer Fest",
        _FESTIVAL,
        date(2026, 9, 12),
        "Crested Butte",
        "CO",
        _STATE_LISTING_URL["CO"],
    ),
    # Illinois (additional)
    _Row(
        "Oak Park Micro Brew Review",
        _FESTIVAL,
        date(2026, 8, 22),
        "Oak Park",
        "IL",
        _STATE_LISTING_URL["IL"],
    ),
    _Row(
        "Springfield Oyster and Beer Festival",
        _FESTIVAL,
        date(2026, 9, 5),
        "Springfield",
        "IL",
        _STATE_LISTING_URL["IL"],
    ),
    _Row(
        "Elmhurst Craft Beer Fest",
        _FESTIVAL,
        date(2026, 9, 19),
        "Elmhurst",
        "IL",
        _STATE_LISTING_URL["IL"],
    ),
    _Row(
        "Big Muddy Monster Brewfest",
        _FESTIVAL,
        date(2026, 10, 3),
        "Murphysboro",
        "IL",
        _STATE_LISTING_URL["IL"],
    ),
    # Virginia
    _Row(
        "Rockbridge Beer & Wine Festival",
        _FESTIVAL,
        date(2026, 9, 12),
        "Lexington",
        "VA",
        _STATE_LISTING_URL["VA"],
    ),
    _Row(
        "757 Battle of the Beers",
        _FESTIVAL,
        date(2026, 9, 12),
        "Virginia Beach",
        "VA",
        _STATE_LISTING_URL["VA"],
    ),
    # Massachusetts (additional)
    _Row(
        "Assabet Craft Beer & Food Truck Festival",
        _FESTIVAL,
        date(2026, 9, 5),
        "Stow",
        "MA",
        _STATE_LISTING_URL["MA"],
    ),
    _Row(
        "Blackburn Brew Fest",
        _FESTIVAL,
        date(2026, 9, 12),
        "Gloucester",
        "MA",
        _STATE_LISTING_URL["MA"],
    ),
    _Row(
        "Cape Cod Brew Fest",
        _FESTIVAL,
        date(2026, 9, 19),
        "East Falmouth",
        "MA",
        _STATE_LISTING_URL["MA"],
    ),
    _Row(
        "South Shore Farmer Brewfest",
        _FESTIVAL,
        date(2026, 10, 11),
        "Bridgewater",
        "MA",
        _STATE_LISTING_URL["MA"],
    ),
    # Florida (additional)
    _Row(
        "Emerald Coast Beer Festival",
        _FESTIVAL,
        date(2026, 9, 11),
        "Pensacola",
        "FL",
        _STATE_LISTING_URL["FL"],
    ),
    _Row(
        "Island Hop Craft Beer & Spirits Fest",
        _FESTIVAL,
        date(2026, 10, 4),
        "Fernandina Beach",
        "FL",
        _STATE_LISTING_URL["FL"],
    ),
    _Row(
        "Baytowne Wharf Beer Festival",
        _FESTIVAL,
        date(2026, 10, 16),
        "Miramar Beach",
        "FL",
        _STATE_LISTING_URL["FL"],
        "Multi-day event.",
    ),
    _Row(
        "Bonita Brew Fest",
        _FESTIVAL,
        date(2027, 2, 20),
        "Bonita Springs",
        "FL",
        _STATE_LISTING_URL["FL"],
    ),
    # New Jersey (additional)
    _Row(
        "Central Jersey Beverage Fest",
        _FESTIVAL,
        date(2026, 9, 26),
        "West Windsor Township",
        "NJ",
        _STATE_LISTING_URL["NJ"],
    ),
    _Row(
        "Uncorked and Uncapped: Wine, Beer, and Food Tasting Fundraiser and Silent Auction",
        _TASTING,
        date(2026, 10, 1),
        "East Hanover",
        "NJ",
        _STATE_LISTING_URL["NJ"],
    ),
    _Row(
        "Witch-Craft",
        _FESTIVAL,
        date(2026, 10, 9),
        "Hammonton",
        "NJ",
        _STATE_LISTING_URL["NJ"],
        "Multi-day event.",
    ),
    # Michigan (additional)
    _Row(
        "Suds on the Shore Craft Beer + Wine Festival",
        _FESTIVAL,
        date(2026, 8, 15),
        "Ludington",
        "MI",
        _STATE_LISTING_URL["MI"],
    ),
    _Row(
        "Burning Foot Beer Festival",
        _FESTIVAL,
        date(2026, 8, 29),
        "Muskegon",
        "MI",
        _STATE_LISTING_URL["MI"],
    ),
    _Row(
        "MI Brewers Guild U.P. Fall Beer Festival",
        _FESTIVAL,
        date(2026, 9, 12),
        None,
        "MI",
        _STATE_LISTING_URL["MI"],
    ),
    _Row(
        "Wyandotte Beer Fest",
        _FESTIVAL,
        date(2026, 9, 18),
        "Wyandotte",
        "MI",
        _STATE_LISTING_URL["MI"],
    ),
    _Row(
        "Grand Ledge Beer Fest",
        _FESTIVAL,
        date(2026, 10, 3),
        "Grand Ledge",
        "MI",
        _STATE_LISTING_URL["MI"],
    ),
    # Minnesota
    _Row(
        "Autumn Brew Review",
        _FESTIVAL,
        date(2026, 10, 10),
        "Minneapolis",
        "MN",
        _STATE_LISTING_URL["MN"],
    ),
    # Maryland
    _Row(
        "Maryland Microbrewery Festival",
        _FESTIVAL,
        date(2026, 9, 26),
        "Westminster",
        "MD",
        _STATE_LISTING_URL["MD"],
    ),
    _Row(
        "Rocktobierfest",
        _FESTIVAL,
        date(2026, 9, 26),
        "Rockville",
        "MD",
        _STATE_LISTING_URL["MD"],
    ),
    _Row(
        "Frederick Oktoberfest",
        _FESTIVAL,
        date(2026, 10, 2),
        "Frederick",
        "MD",
        _STATE_LISTING_URL["MD"],
        "Multi-day event.",
    ),
    _Row(
        "Good Beer Festival",
        _FESTIVAL,
        date(2026, 10, 9),
        "Salisbury",
        "MD",
        _STATE_LISTING_URL["MD"],
        "Multi-day event.",
    ),
    _Row(
        "Patterson Park BrewFest",
        _FESTIVAL,
        date(2026, 11, 7),
        "Baltimore",
        "MD",
        _STATE_LISTING_URL["MD"],
    ),
    # Vermont
    _Row(
        "Vermont NanoFest",
        _FESTIVAL,
        date(2026, 8, 15),
        "Tunbridge",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "Mount Snow Brewers Festival",
        _FESTIVAL,
        date(2026, 9, 5),
        "West Dover",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "Trapp Family Lodge Oktoberfest",
        _FESTIVAL,
        date(2026, 9, 19),
        "Stowe",
        "VT",
        _STATE_LISTING_URL["VT"],
        "Multi-day event.",
    ),
    _Row(
        "Harvest Festival of Ales and Lagers",
        _FESTIVAL,
        date(2026, 9, 19),
        "Greensboro Bend",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "SIPtemberfest",
        _FESTIVAL,
        date(2026, 9, 19),
        "Waitsfield",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "Killington Brewfest",
        _FESTIVAL,
        date(2026, 9, 26),
        "Killington",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "Sugarbush Oktoberfest",
        _FESTIVAL,
        date(2026, 10, 10),
        "Warren",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "Stratton Harvestfest Brewfest & Chili Cookoff",
        _FESTIVAL,
        date(2026, 10, 10),
        "South Londonderry",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    _Row(
        "Bean and Brew Festival",
        _FESTIVAL,
        date(2026, 10, 17),
        "Jay Peak",
        "VT",
        _STATE_LISTING_URL["VT"],
    ),
    # Maine
    _Row(
        "Skowhegan Craft Brew Festival",
        _FESTIVAL,
        date(2026, 9, 5),
        "Skowhegan",
        "ME",
        _STATE_LISTING_URL["ME"],
    ),
    _Row(
        "Swine & Stein Brewfest",
        _FESTIVAL,
        date(2026, 10, 10),
        "Gardiner",
        "ME",
        _STATE_LISTING_URL["ME"],
    ),
    # Indiana
    _Row(
        "Hops & Coaster Drops",
        _FESTIVAL,
        date(2026, 9, 12),
        "Monticello",
        "IN",
        _STATE_LISTING_URL["IN"],
    ),
    # Tennessee
    _Row(
        "Music City Brewer's Festival",
        _FESTIVAL,
        date(2026, 8, 22),
        "Nashville",
        "TN",
        _STATE_LISTING_URL["TN"],
    ),
    _Row(
        "Nashville Oktoberfest",
        _FESTIVAL,
        date(2026, 10, 1),
        "Nashville",
        "TN",
        _STATE_LISTING_URL["TN"],
        "Multi-day event.",
    ),
    _Row(
        "Tennessee Beer, Wine and Shine Festival",
        _FESTIVAL,
        date(2026, 10, 17),
        "Nashville",
        "TN",
        _STATE_LISTING_URL["TN"],
    ),
    _Row(
        "Kill the Lights Beer Festival",
        _FESTIVAL,
        date(2026, 10, 24),
        "Knoxville",
        "TN",
        _STATE_LISTING_URL["TN"],
    ),
]


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _slug_for(row: _Row) -> str:
    year = row.event_date.year if row.event_date else "tbd"
    return f"{_slugify(row.name)}-{year}"[:220]


async def seed_festivals() -> None:
    async with session_scope() as session:
        repo = FestivalRepository(session)
        added = updated = 0
        for row in _ROWS:
            slug = _slug_for(row)
            existing = await repo.get_by_slug(slug)
            if existing is None:
                await repo.add(
                    Festival(
                        slug=slug,
                        name=row.name,
                        category=row.category,
                        event_date=row.event_date,
                        city=row.city,
                        state=row.state,
                        description=row.description,
                        url=row.url,
                        source="beerfests.com",
                    )
                )
                added += 1
            else:
                existing.name = row.name
                existing.category = row.category
                existing.event_date = row.event_date
                existing.city = row.city
                existing.state = row.state
                existing.description = row.description
                existing.url = row.url
                updated += 1
        logger.info("Festivals seeded", extra={"added": added, "updated": updated})
        print(f"Festivals: {added} added, {updated} updated (of {len(_ROWS)} total).")


if __name__ == "__main__":
    asyncio.run(seed_festivals())
