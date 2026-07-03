"""BrewIQ scores: brewery_scores.

Revision ID: 0003_brewery_scores
Revises: 0002_diff_engine
Create Date: 2026-07-03
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_brewery_scores"
down_revision: str | None = "0002_diff_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brewery_scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("brewery_id", sa.Uuid(), nullable=False),
        sa.Column("overall", sa.Float(), nullable=False),
        sa.Column("data_confidence", sa.Float(), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("trend_direction", sa.String(length=10), nullable=False),
        sa.Column("trend_delta", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["brewery_id"], ["breweries.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_brewery_scores_brewery_id", "brewery_scores", ["brewery_id"])


def downgrade() -> None:
    op.drop_index("ix_brewery_scores_brewery_id", table_name="brewery_scores")
    op.drop_table("brewery_scores")
