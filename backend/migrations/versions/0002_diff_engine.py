"""Diff engine: extractions and change_events.

Revision ID: 0002_diff_engine
Revises: 0001_initial
Create Date: 2026-07-03
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_diff_engine"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHANGE_EVENT_TYPES = (
    "beer_added",
    "beer_removed",
    "beer_abv_changed",
    "beer_description_changed",
    "event_added",
    "event_removed",
    "food_truck_added",
    "food_truck_removed",
    "hours_changed",
)


def upgrade() -> None:
    op.create_table(
        "extractions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("discovered_url_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["discovered_url_id"], ["discovered_urls.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_extractions_discovered_url_id", "extractions", ["discovered_url_id"])

    change_event_type = sa.Enum(*_CHANGE_EVENT_TYPES, name="change_event_type")
    op.create_table(
        "change_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("brewery_id", sa.Uuid(), nullable=False),
        sa.Column("discovered_url_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", change_event_type, nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["brewery_id"], ["breweries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discovered_url_id"], ["discovered_urls.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_change_events_brewery_id", "change_events", ["brewery_id"])
    op.create_index("ix_change_events_discovered_url_id", "change_events", ["discovered_url_id"])


def downgrade() -> None:
    op.drop_table("change_events")
    op.drop_index("ix_extractions_discovered_url_id", table_name="extractions")
    op.drop_table("extractions")
    sa.Enum(name="change_event_type").drop(op.get_bind(), checkfirst=True)
