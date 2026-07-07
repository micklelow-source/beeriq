"""Add brewery_type to breweries.

Revision ID: 0004_brewery_type
Revises: 0003_brewery_scores
Create Date: 2026-07-07
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_brewery_type"
down_revision: str | None = "0003_brewery_scores"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("breweries", sa.Column("brewery_type", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("breweries", "brewery_type")
