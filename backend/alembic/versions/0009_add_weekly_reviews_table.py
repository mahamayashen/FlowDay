"""add weekly_reviews table

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-19

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_reviews",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("raw_data_json", postgresql.JSONB(), nullable=False),
        sa.Column("insights_json", postgresql.JSONB(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("scores_json", postgresql.JSONB(), nullable=True),
        sa.Column("agent_metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'generating', 'complete', 'failed')",
            name="ck_weekly_reviews_status",
        ),
    )
    op.create_index(
        "idx_weekly_review_user_week",
        "weekly_reviews",
        ["user_id", "week_start"],
    )


def downgrade() -> None:
    op.drop_index("idx_weekly_review_user_week", table_name="weekly_reviews")
    op.drop_table("weekly_reviews")
