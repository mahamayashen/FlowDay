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
    ProjectWeeklyStats,
    StatusTag,
    TaskComparison,
    WeeklyStatsResponse,
    WeeklyStatsSummary,
)


def align_to_monday(d: date) -> date:
    """Return the Monday of the week containing *d*."""
    return d - timedelta(days=d.weekday())


def compute_accuracy_pct(planned: float, actual: float) -> float:
    """Return estimation accuracy as a percentage.

    Returns 0.0 when planned == 0 to avoid division by zero.
    """
    if planned <= 0:
        return 0.0
    return (actual / planned) * 100


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
    day_start = datetime.combine(query_date, datetime.min.time(), tzinfo=UTC)
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
        row.task_id: (row.title, float(row.planned_hours)) for row in planned_rows
    }
    actual_map: dict[uuid.UUID, tuple[str, float]] = {
        row.task_id: (row.title, float(row.actual_hours)) for row in actual_rows
    }

    all_task_ids = set(planned_map) | set(actual_map)
    comparisons: list[TaskComparison] = []
    for tid in sorted(all_task_ids):
        title = planned_map[tid][0] if tid in planned_map else actual_map[tid][0]
        planned_h = planned_map[tid][1] if tid in planned_map else 0.0
        actual_h = actual_map[tid][1] if tid in actual_map else 0.0
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


async def get_weekly_stats(
    db: AsyncSession,
    user_id: uuid.UUID,
    week_start: date,
) -> WeeklyStatsResponse:
    """Return per-project planned vs actual hours for the week containing week_start."""
    monday = align_to_monday(week_start)
    next_monday = monday + timedelta(days=7)
    sunday = monday + timedelta(days=6)

    # Query 1: planned hours per project from schedule blocks
    planned_stmt = (
        select(
            Project.id,
            Project.name,
            Project.color,
            func.sum(ScheduleBlock.end_hour - ScheduleBlock.start_hour).label(
                "planned_hours"
            ),
        )
        .join(Task, ScheduleBlock.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            ScheduleBlock.date >= monday,
            ScheduleBlock.date < next_monday,
            Project.user_id == user_id,
        )
        .group_by(Project.id, Project.name, Project.color)
    )
    planned_result = await db.execute(planned_stmt)
    planned_rows = planned_result.all()

    # Query 2: actual hours per project from completed time entries
    week_start_dt = datetime.combine(monday, datetime.min.time(), tzinfo=UTC)
    week_end_dt = datetime.combine(next_monday, datetime.min.time(), tzinfo=UTC)
    actual_stmt = (
        select(
            Project.id,
            Project.name,
            Project.color,
            (func.sum(TimeEntry.duration_seconds) / 3600.0).label("actual_hours"),
        )
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            TimeEntry.started_at >= week_start_dt,
            TimeEntry.started_at < week_end_dt,
            TimeEntry.duration_seconds.isnot(None),
            Project.user_id == user_id,
        )
        .group_by(Project.id, Project.name, Project.color)
    )
    actual_result = await db.execute(actual_stmt)
    actual_rows = actual_result.all()

    # Merge in Python
    planned_map: dict[uuid.UUID, tuple[str, str, float]] = {
        row.id: (row.name, row.color, float(row.planned_hours)) for row in planned_rows
    }
    actual_map: dict[uuid.UUID, tuple[str, str, float]] = {
        row.id: (row.name, row.color, float(row.actual_hours)) for row in actual_rows
    }

    all_project_ids = set(planned_map) | set(actual_map)
    projects: list[ProjectWeeklyStats] = []
    for pid in sorted(all_project_ids):
        name = planned_map[pid][0] if pid in planned_map else actual_map[pid][0]
        color = planned_map[pid][1] if pid in planned_map else actual_map[pid][1]
        planned_h = planned_map[pid][2] if pid in planned_map else 0.0
        actual_h = actual_map[pid][2] if pid in actual_map else 0.0
        projects.append(
            ProjectWeeklyStats(
                project_id=pid,
                project_name=name,
                project_color=color,
                planned_hours=planned_h,
                actual_hours=actual_h,
                accuracy_pct=compute_accuracy_pct(planned_h, actual_h),
            )
        )

    # Average accuracy — only projects where planned > 0
    projects_with_plan = [p for p in projects if p.planned_hours > 0]
    average_accuracy = (
        sum(p.accuracy_pct for p in projects_with_plan) / len(projects_with_plan)
        if projects_with_plan
        else 0.0
    )

    summary = WeeklyStatsSummary(
        total_planned_hours=sum(p.planned_hours for p in projects),
        total_actual_hours=sum(p.actual_hours for p in projects),
        average_accuracy_pct=average_accuracy,
    )

    return WeeklyStatsResponse(
        week_start=monday,
        week_end=sunday,
        projects=projects,
        summary=summary,
    )
