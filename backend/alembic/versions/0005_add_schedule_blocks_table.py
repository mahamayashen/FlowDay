"""add schedule_blocks table

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-15

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedule_blocks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            sa.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_hour", sa.Numeric(4, 2), nullable=False),
        sa.Column("end_hour", sa.Numeric(4, 2), nullable=False),
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source IN ('manual', 'google_calendar')",
            name="ck_schedule_blocks_source",
        ),
        sa.CheckConstraint(
            "end_hour > start_hour",
            name="ck_schedule_blocks_end_gt_start",
        ),
    )
    op.create_index("idx_schedule_block_date", "schedule_blocks", ["date", "task_id"])


def downgrade() -> None:
    op.drop_index("idx_schedule_block_date", table_name="schedule_blocks")
    op.drop_table("schedule_blocks")
