"""Initial schema: breweries, discovered_urls, page_snapshots.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-02
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PAGE_TYPES = ("tap", "beer", "menu", "events", "food_truck", "home", "unknown")


def upgrade() -> None:
    op.create_table(
        "breweries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_breweries_slug"),
    )
    op.create_index("ix_breweries_slug", "breweries", ["slug"])
    op.create_index("ix_breweries_state", "breweries", ["state"])

    page_type = sa.Enum(*_PAGE_TYPES, name="page_type")
    op.create_table(
        "discovered_urls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("brewery_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("page_type", page_type, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["brewery_id"], ["breweries.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brewery_id", "url", name="uq_discovered_urls_brewery_url"),
    )
    op.create_index("ix_discovered_urls_brewery_id", "discovered_urls", ["brewery_id"])

    op.create_table(
        "page_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("discovered_url_id", sa.Uuid(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("html", sa.Text(), nullable=True),
        sa.Column("etag", sa.String(length=256), nullable=True),
        sa.Column("last_modified", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["discovered_url_id"], ["discovered_urls.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_page_snapshots_discovered_url_id", "page_snapshots", ["discovered_url_id"])
    op.create_index("ix_page_snapshots_content_hash", "page_snapshots", ["content_hash"])


def downgrade() -> None:
    op.drop_table("page_snapshots")
    op.drop_table("discovered_urls")
    op.drop_index("ix_breweries_state", table_name="breweries")
    op.drop_index("ix_breweries_slug", table_name="breweries")
    op.drop_table("breweries")
    sa.Enum(name="page_type").drop(op.get_bind(), checkfirst=True)
