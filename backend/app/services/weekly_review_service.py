"""WeeklyReview service — orchestrates the full AI pipeline and persists results."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import run_group_a, run_group_b, run_group_c, run_group_d
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


async def get_review(
    db: AsyncSession,
    user_id: uuid.UUID,
    week_start: date,
) -> WeeklyReview | None:
    """Return the WeeklyReview for this user/week, or None if it doesn't exist.

    Args:
        db: Async database session.
        user_id: Owner of the review.
        week_start: Any date in the target week — clamped to Monday automatically.

    Returns:
        Existing WeeklyReview or None.
    """
    monday = _align_to_monday(week_start)
    result = await db.execute(
        select(WeeklyReview).where(
            WeeklyReview.user_id == user_id,
            WeeklyReview.week_start == monday,
        )
    )
    return result.scalar_one_or_none()


async def generate_review(
    db: AsyncSession,
    review: WeeklyReview,
    analysis_date: date,
) -> WeeklyReview:
    """Run the full A→B→C→D agent pipeline and persist results on the review.

    Sets status to 'generating' before the pipeline starts and 'complete' on
    success, or 'failed' if any stage raises. The exception is re-raised after
    the failed status is flushed.

    Args:
        db: Async database session.
        review: The WeeklyReview record to populate (must already be persisted).
        analysis_date: Reference date passed to all agents.

    Returns:
        The updated WeeklyReview with narrative, scores, and metadata populated.
    """
    review.status = ReviewStatus.GENERATING
    await db.flush()

    try:
        group_a_result = await run_group_a(db, review.user_id, analysis_date)
        pattern_result = await run_group_b(
            group_a_result, review.user_id, analysis_date
        )
        narrative_result = await run_group_c(
            group_a_result, pattern_result, review.user_id, analysis_date
        )
        judge_result = await run_group_d(
            db,
            group_a_result,
            pattern_result,
            narrative_result,
            review.user_id,
            analysis_date,
        )
    except Exception:
        review.status = ReviewStatus.FAILED
        await db.flush()
        raise

    review.insights_json = group_a_result.model_dump()
    review.narrative = (
        f"{narrative_result.executive_summary}\n\n"
        f"{narrative_result.time_analysis}\n\n"
        f"{narrative_result.productivity_patterns}\n\n"
        f"{narrative_result.areas_of_concern}"
    )
    review.scores_json = judge_result.model_dump() if judge_result is not None else None
    review.agent_metadata_json = {
        "analysis_date": analysis_date.isoformat(),
        "patterns_detected": len(pattern_result.patterns),
        "group_a_errors": group_a_result.errors,
        "judge_scored": judge_result is not None,
    }
    review.status = ReviewStatus.COMPLETE
    await db.flush()
    return review
