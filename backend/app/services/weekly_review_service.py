"""WeeklyReview service — orchestrates the full AI pipeline and persists results."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weekly_review import ReviewStatus, WeeklyReview


def _align_to_monday(d: date) -> date:
    """Return the Monday of the week containing *d*."""
    return d - timedelta(days=d.weekday())


async def get_or_create_review(
    db: AsyncSession,
    user_id: uuid.UUID,
    week_start: date,
) -> WeeklyReview:
    """Return the existing WeeklyReview for this user/week or create a new pending one.

    Args:
        db: Async database session.
        user_id: Owner of the review.
        week_start: Any date in the target week — clamped to Monday automatically.

    Returns:
        Existing or newly-created WeeklyReview with status=pending.
    """
    monday = _align_to_monday(week_start)

    result = await db.execute(
        select(WeeklyReview).where(
            WeeklyReview.user_id == user_id,
            WeeklyReview.week_start == monday,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    review = WeeklyReview(
        user_id=user_id,
        week_start=monday,
        raw_data_json={},
    )
    db.add(review)
    await db.flush()
    return review
