"""add external_syncs table

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_syncs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "sync_config_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "provider IN ('google_calendar', 'github')",
            name="ck_external_syncs_provider",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'error')",
            name="ck_external_syncs_status",
        ),
    )
    op.create_index(
        "idx_external_sync_user_provider",
        "external_syncs",
        ["user_id", "provider"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_external_sync_user_provider", table_name="external_syncs")
    op.drop_table("external_syncs")
