from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SyncProvider(enum.StrEnum):
    """Supported external sync providers."""

    GOOGLE_CALENDAR = "google_calendar"
    GITHUB = "github"


class SyncStatus(enum.StrEnum):
    """Sync connection lifecycle status."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class ExternalSync(Base):
    """ExternalSync entity -- see docs/DATA_MODEL.md for full specification."""

    __tablename__ = "external_syncs"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('google_calendar', 'github')",
            name="ck_external_syncs_provider",
        ),
        CheckConstraint(
            "status IN ('active', 'paused', 'error')",
            name="ck_external_syncs_status",
        ),
        Index("idx_external_sync_user_provider", "user_id", "provider", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_config_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SyncStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<ExternalSync(id={self.id}, provider={self.provider})>"
