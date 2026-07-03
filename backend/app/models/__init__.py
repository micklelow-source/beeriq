"""SQLAlchemy ORM models.

Importing this package registers every model on :data:`Base.metadata`, which
Alembic and the test harness rely on for schema creation.
"""

from app.models.base import Base
from app.models.brewery import Brewery
from app.models.change_event import ChangeEvent, ChangeEventType
from app.models.discovered_url import DiscoveredURL, PageType
from app.models.extraction import Extraction
from app.models.page_snapshot import PageSnapshot

__all__ = [
    "Base",
    "Brewery",
    "ChangeEvent",
    "ChangeEventType",
    "DiscoveredURL",
    "Extraction",
    "PageType",
    "PageSnapshot",
]
