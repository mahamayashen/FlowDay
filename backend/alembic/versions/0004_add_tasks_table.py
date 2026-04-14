"""add tasks table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-13

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "project_id", sa.UUID(), sa.ForeignKey("projects.id"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("estimate_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "priority",
            sa.String(20),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="todo",
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="ck_tasks_priority",
        ),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'done')",
            name="ck_tasks_status",
        ),
    )
    op.create_index("idx_task_project_status", "tasks", ["project_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_task_project_status", table_name="tasks")
    op.drop_table("tasks")
