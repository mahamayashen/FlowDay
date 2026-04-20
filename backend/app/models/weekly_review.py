"""WeeklyReview model — persists AI-generated weekly review outputs."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReviewStatus(enum.StrEnum):
    """Lifecycle status of a WeeklyReview generation run."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


_VALID_STATUSES = "('pending', 'generating', 'complete', 'failed')"


class WeeklyReview(Base):
    """WeeklyReview entity — see docs/DATA_MODEL.md for full specification."""

    __tablename__ = "weekly_reviews"
    __table_args__ = (
        CheckConstraint(
            f"status IN {_VALID_STATUSES}",
            name="ck_weekly_reviews_status",
        ),
        Index("idx_weekly_review_user_week", "user_id", "week_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    raw_data_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    insights_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    scores_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    agent_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ReviewStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("status", ReviewStatus.PENDING)
        kwargs.setdefault("created_at", datetime.now(UTC))
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<WeeklyReview(user_id={self.user_id}, week_start={self.week_start}, "
            f"status={self.status})>"
        )
