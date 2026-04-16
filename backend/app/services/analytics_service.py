from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.schedule_block import ScheduleBlock
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.schemas.analytics import (
    PlannedVsActualResponse,
    PlannedVsActualSummary,
    StatusTag,
    TaskComparison,
)


def compute_status_tag(planned_hours: float, actual_hours: float) -> StatusTag:
    """Determine the status tag for a single task comparison.

    Pure function — no DB access.
    """
    if planned_hours > 0:
        if actual_hours >= 0.9 * planned_hours:
            return StatusTag.DONE
        if actual_hours > 0:
            return StatusTag.PARTIAL
        return StatusTag.SKIPPED
    if actual_hours > 0:
        return StatusTag.UNPLANNED
    return StatusTag.SKIPPED


async def get_planned_vs_actual(
    db: AsyncSession,
    user_id: uuid.UUID,
    query_date: date,
) -> PlannedVsActualResponse:
    """Build a planned-vs-actual comparison for a single day."""
    # Query 1: planned hours per task from schedule blocks
    planned_stmt = (
        select(
            ScheduleBlock.task_id,
            Task.title,
            func.sum(ScheduleBlock.end_hour - ScheduleBlock.start_hour).label(
                "planned_hours"
            ),
        )
        .join(Task, ScheduleBlock.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(ScheduleBlock.date == query_date, Project.user_id == user_id)
        .group_by(ScheduleBlock.task_id, Task.title)
    )
    planned_result = await db.execute(planned_stmt)
    planned_rows = planned_result.all()

    # Query 2: actual hours per task from completed time entries
    day_start = datetime(
        query_date.year, query_date.month, query_date.day, tzinfo=UTC
    )
    day_end = day_start + timedelta(days=1)
    actual_stmt = (
        select(
            TimeEntry.task_id,
            Task.title,
            (func.sum(TimeEntry.duration_seconds) / 3600.0).label("actual_hours"),
        )
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            TimeEntry.started_at >= day_start,
            TimeEntry.started_at < day_end,
            TimeEntry.duration_seconds.isnot(None),
            Project.user_id == user_id,
        )
        .group_by(TimeEntry.task_id, Task.title)
    )
    actual_result = await db.execute(actual_stmt)
    actual_rows = actual_result.all()

    # Merge in Python
    planned_map: dict[uuid.UUID, tuple[str, float]] = {
        row.task_id: (row.title, float(row.planned_hours))
        for row in planned_rows
    }
    actual_map: dict[uuid.UUID, tuple[str, float]] = {
        row.task_id: (row.title, float(row.actual_hours))
        for row in actual_rows
    }

    all_task_ids = set(planned_map) | set(actual_map)
    comparisons: list[TaskComparison] = []
    for tid in sorted(all_task_ids):
        title = planned_map.get(tid, (None, 0.0))[0] or actual_map[tid][0]
        planned_h = planned_map.get(tid, ("", 0.0))[1]
        actual_h = actual_map.get(tid, ("", 0.0))[1]
        comparisons.append(
            TaskComparison(
                task_id=tid,
                task_title=title,
                planned_hours=planned_h,
                actual_hours=actual_h,
                status=compute_status_tag(planned_h, actual_h),
            )
        )

    # Build summary
    summary = PlannedVsActualSummary(
        total_planned_hours=sum(t.planned_hours for t in comparisons),
        total_actual_hours=sum(t.actual_hours for t in comparisons),
        done_count=sum(1 for t in comparisons if t.status == StatusTag.DONE),
        partial_count=sum(1 for t in comparisons if t.status == StatusTag.PARTIAL),
        skipped_count=sum(1 for t in comparisons if t.status == StatusTag.SKIPPED),
        unplanned_count=sum(1 for t in comparisons if t.status == StatusTag.UNPLANNED),
    )

    return PlannedVsActualResponse(
        date=query_date,
        tasks=comparisons,
        summary=summary,
    )
