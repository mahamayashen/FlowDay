from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import PlannedVsActualResponse, WeeklyStatsResponse
from app.services.analytics_service import get_planned_vs_actual, get_weekly_stats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/planned-vs-actual", response_model=PlannedVsActualResponse)
async def planned_vs_actual_route(
    query_date: date = Query(..., alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlannedVsActualResponse:
    """Return planned-vs-actual comparison for a single day."""
    return await get_planned_vs_actual(
        db=db, user_id=current_user.id, query_date=query_date
    )


@router.get("/weekly-stats", response_model=WeeklyStatsResponse)
async def weekly_stats_route(
    week_start: date = Query(..., alias="week_start"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyStatsResponse:
    """Return per-project weekly stats for the week containing week_start."""
    return await get_weekly_stats(
        db=db, user_id=current_user.id, week_start=week_start
    )
