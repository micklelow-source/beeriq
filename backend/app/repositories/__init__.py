"""Data-access layer. Repositories are the only code that issues queries."""

from app.repositories.brewery import BreweryRepository
from app.repositories.brewery_score import BreweryScoreRepository
from app.repositories.change_event import ChangeEventRepository
from app.repositories.discovered_url import DiscoveredURLRepository
from app.repositories.extraction import ExtractionRepository
from app.repositories.page_snapshot import PageSnapshotRepository

__all__ = [
    "BreweryRepository",
    "BreweryScoreRepository",
    "ChangeEventRepository",
    "DiscoveredURLRepository",
    "ExtractionRepository",
    "PageSnapshotRepository",
]
