"""Weekly review API routes — trigger generation and fetch stored reviews."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.weekly_review import WeeklyReviewResponse
from app.services.weekly_review_service import (
    generate_review,
    get_or_create_review,
    get_review_by_id,
    list_reviews,
)

router = APIRouter(prefix="/weekly-reviews", tags=["weekly-reviews"])


@router.post("/generate", response_model=WeeklyReviewResponse)
async def trigger_weekly_review(
    week_start: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyReviewResponse:
    """Trigger AI generation of the weekly review for the given week.

    If a review already exists for this week, it is re-generated in place.
    """
    review = await get_or_create_review(db, current_user.id, week_start)
    review = await generate_review(db, review, week_start)
    return WeeklyReviewResponse.model_validate(review)


@router.get("", response_model=list[WeeklyReviewResponse])
async def list_weekly_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeeklyReviewResponse]:
    """Return all weekly reviews owned by the current user, newest week first."""
    reviews = await list_reviews(db, current_user.id)
    return [WeeklyReviewResponse.model_validate(r) for r in reviews]


@router.get("/{review_id}", response_model=WeeklyReviewResponse)
async def fetch_weekly_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyReviewResponse:
    """Return a single stored weekly review by id, scoped to the current user."""
    review = await get_review_by_id(db, current_user.id, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Weekly review not found")
    return WeeklyReviewResponse.model_validate(review)
