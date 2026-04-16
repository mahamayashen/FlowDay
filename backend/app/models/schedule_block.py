from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScheduleBlockSource(enum.StrEnum):
    """Source of the schedule block."""

    MANUAL = "manual"
    GOOGLE_CALENDAR = "google_calendar"


class ScheduleBlock(Base):
    """Schedule block entity — see docs/DATA_MODEL.md for full specification."""

    __tablename__ = "schedule_blocks"
    __table_args__ = (
        CheckConstraint(
            "source IN ('manual', 'google_calendar')",
            name="ck_schedule_blocks_source",
        ),
        CheckConstraint(
            "end_hour > start_hour",
            name="ck_schedule_blocks_end_gt_start",
        ),
        Index("idx_schedule_block_date", "date", "task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    start_hour: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    end_hour: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ScheduleBlockSource.MANUAL,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<ScheduleBlock(id={self.id})>"
