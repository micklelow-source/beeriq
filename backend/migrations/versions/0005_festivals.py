"""Add festivals table.

Revision ID: 0005_festivals
Revises: 0004_brewery_type
Create Date: 2026-08-13
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_festivals"
down_revision: str | None = "0004_brewery_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FESTIVAL_CATEGORIES = ("festival", "tasting")


def upgrade() -> None:
    category = sa.Enum(*_FESTIVAL_CATEGORIES, name="festival_category")
    op.create_table(
        "festivals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", category, nullable=False, server_default="festival"),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="beerfests.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_festivals_slug"),
    )
    op.create_index("ix_festivals_slug", "festivals", ["slug"])
    op.create_index("ix_festivals_state", "festivals", ["state"])


def downgrade() -> None:
    op.drop_index("ix_festivals_state", table_name="festivals")
    op.drop_index("ix_festivals_slug", table_name="festivals")
    op.drop_table("festivals")
    sa.Enum(name="festival_category").drop(op.get_bind(), checkfirst=True)
