"""add agent_score_history table

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-19

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_score_history",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("actionability_score", sa.Integer(), nullable=False),
        sa.Column("accuracy_score", sa.Integer(), nullable=False),
        sa.Column("coherence_score", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "actionability_score BETWEEN 1 AND 10",
            name="ck_agent_score_history_actionability",
        ),
        sa.CheckConstraint(
            "accuracy_score BETWEEN 1 AND 10",
            name="ck_agent_score_history_accuracy",
        ),
        sa.CheckConstraint(
            "coherence_score BETWEEN 1 AND 10",
            name="ck_agent_score_history_coherence",
        ),
        sa.CheckConstraint(
            "overall_score BETWEEN 1 AND 10",
            name="ck_agent_score_history_overall",
        ),
    )
    op.create_index(
        "idx_agent_score_history_user_date",
        "agent_score_history",
        ["user_id", "analysis_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_agent_score_history_user_date",
        table_name="agent_score_history",
    )
    op.drop_table("agent_score_history")
