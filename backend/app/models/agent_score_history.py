"""AgentScoreHistory model — stores Judge agent scores for trend analysis."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_SCORE_RANGE = "BETWEEN 1 AND 10"


class AgentScoreHistory(Base):
    """Persisted Judge scores per user per analysis date."""

    __tablename__ = "agent_score_history"
    __table_args__ = (
        Index("idx_agent_score_history_user_date", "user_id", "analysis_date"),
        CheckConstraint(
            f"actionability_score {_SCORE_RANGE}",
            name="ck_agent_score_history_actionability",
        ),
        CheckConstraint(
            f"accuracy_score {_SCORE_RANGE}",
            name="ck_agent_score_history_accuracy",
        ),
        CheckConstraint(
            f"coherence_score {_SCORE_RANGE}",
            name="ck_agent_score_history_coherence",
        ),
        CheckConstraint(
            f"overall_score {_SCORE_RANGE}",
            name="ck_agent_score_history_overall",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    actionability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_score: Mapped[int] = mapped_column(Integer, nullable=False)
    coherence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"<AgentScoreHistory(user_id={self.user_id}, "
            f"date={self.analysis_date}, overall={self.overall_score})>"
        )
