"""Group A orchestrator — runs four parallel analyst agents via asyncio.gather."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any, TypeVar

from pydantic_ai import Agent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_analyst import code_analyst
from app.agents.meeting_analyst import meeting_analyst
from app.agents.schemas import (
    CodeAnalystDeps,
    GitHubSyncData,
    GroupAResult,
    MeetingAnalystDeps,
    ScheduleBlockData,
    TaskAnalystDeps,
    TaskData,
    TimeAnalystDeps,
    TimeEntryData,
)
from app.agents.task_analyst import task_analyst
from app.agents.time_analyst import time_analyst
from app.core.metrics import agent_latency_seconds
from app.models.external_sync import ExternalSync, SyncProvider
from app.models.project import Project
from app.models.schedule_block import ScheduleBlock
from app.models.task import Task
from app.models.time_entry import TimeEntry

log = logging.getLogger(__name__)

_AgentResultT = TypeVar("_AgentResultT")


async def _run_agent(
    agent: Agent[Any, _AgentResultT],
    name: str,
    deps: Any,
) -> _AgentResultT:
    """Run a single agent, recording latency and propagating errors."""
    start = time.perf_counter()
    try:
        result = await agent.run("Analyze and produce structured insights.", deps=deps)
        return result.output
    finally:
        elapsed = time.perf_counter() - start
        agent_latency_seconds.labels(agent_name=name).observe(elapsed)


async def run_group_a(
    db: AsyncSession,
    user_id: uuid.UUID,
    analysis_date: date,
) -> GroupAResult:
    """Run all four Group A analyst agents in parallel and return aggregated results.

    Args:
        db: Async database session for pre-fetching data.
        user_id: The user whose data to analyze.
        analysis_date: The reference date for the analysis.

    Returns:
        GroupAResult with individual agent outputs and any errors encountered.
    """
    time_entries, schedule_blocks, tasks, github_sync = await asyncio.gather(
        _fetch_time_entries(db, user_id, analysis_date),
        _fetch_schedule_blocks(db, user_id, analysis_date),
        _fetch_tasks(db, user_id),
        _fetch_github_sync(db, user_id),
    )

    calendar_blocks = [b for b in schedule_blocks if b.source == "google_calendar"]

    time_deps = TimeAnalystDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        time_entries=time_entries,
        schedule_blocks=[b for b in schedule_blocks if b.source == "manual"],
    )
    meeting_deps = MeetingAnalystDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        calendar_blocks=calendar_blocks,
    )
    code_deps = CodeAnalystDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        github_sync=github_sync,
    )
    task_deps = TaskAnalystDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        tasks=tasks,
    )

    errors: dict[str, str] = {}

    async def _safe_run(agent: Agent[Any, Any], name: str, deps: Any) -> Any:
        try:
            return await _run_agent(agent, name, deps)
        except Exception as exc:
            log.error("Agent %s failed: %s", name, exc)
            errors[name] = str(exc)
            return None

    time_result, meeting_result, code_result, task_result = await asyncio.gather(
        _safe_run(time_analyst, "time_analyst", time_deps),
        _safe_run(meeting_analyst, "meeting_analyst", meeting_deps),
        _safe_run(code_analyst, "code_analyst", code_deps),
        _safe_run(task_analyst, "task_analyst", task_deps),
    )

    return GroupAResult(
        time_analysis=time_result,
        meeting_analysis=meeting_result,
        code_analysis=code_result,
        task_analysis=task_result,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Private data-fetching helpers
# ---------------------------------------------------------------------------


async def _fetch_time_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    analysis_date: date,
) -> list[TimeEntryData]:
    """Fetch time entries for the given user on the analysis date."""
    day_start = datetime.combine(analysis_date, datetime.min.time(), tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    stmt = (
        select(
            TimeEntry.task_id,
            Task.title.label("task_title"),
            Project.name.label("project_name"),
            TimeEntry.started_at,
            TimeEntry.ended_at,
            TimeEntry.duration_seconds,
        )
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            TimeEntry.started_at >= day_start,
            TimeEntry.started_at < day_end,
            TimeEntry.duration_seconds > 0,
            Project.user_id == user_id,
        )
    )
    rows = (await db.execute(stmt)).all()
    return [
        TimeEntryData(
            task_id=row.task_id,
            task_title=row.task_title,
            project_name=row.project_name,
            started_at=row.started_at,
            ended_at=row.ended_at,
            duration_seconds=row.duration_seconds,
        )
        for row in rows
    ]


async def _fetch_schedule_blocks(
    db: AsyncSession,
    user_id: uuid.UUID,
    analysis_date: date,
) -> list[ScheduleBlockData]:
    """Fetch schedule blocks for the given user on the analysis date."""
    stmt = (
        select(
            ScheduleBlock.task_id,
            Task.title.label("task_title"),
            ScheduleBlock.date,
            ScheduleBlock.start_hour,
            ScheduleBlock.end_hour,
            ScheduleBlock.source,
        )
        .join(Task, ScheduleBlock.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            ScheduleBlock.date == analysis_date,
            Project.user_id == user_id,
        )
    )
    rows = (await db.execute(stmt)).all()
    return [
        ScheduleBlockData(
            task_id=row.task_id,
            task_title=row.task_title,
            date=row.date,
            start_hour=float(row.start_hour),
            end_hour=float(row.end_hour),
            source=row.source.value if hasattr(row.source, "value") else row.source,
        )
        for row in rows
    ]


async def _fetch_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[TaskData]:
    """Fetch all active tasks for the given user."""
    stmt = (
        select(
            Task.id.label("task_id"),
            Task.title,
            Project.name.label("project_name"),
            Task.status,
            Task.priority,
            Task.estimate_minutes,
            Task.due_date,
            Task.created_at,
            Task.completed_at,
        )
        .join(Project, Task.project_id == Project.id)
        .where(Project.user_id == user_id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        TaskData(
            task_id=row.task_id,
            title=row.title,
            project_name=row.project_name,
            status=row.status.value if hasattr(row.status, "value") else row.status,
            priority=row.priority.value if hasattr(row.priority, "value") else row.priority,
            estimate_minutes=row.estimate_minutes,
            due_date=row.due_date,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )
        for row in rows
    ]


async def _fetch_github_sync(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> GitHubSyncData | None:
    """Fetch the GitHub ExternalSync record for the given user, if it exists."""
    stmt = select(ExternalSync).where(
        ExternalSync.user_id == user_id,
        ExternalSync.provider == SyncProvider.GITHUB,
    )
    result = (await db.execute(stmt)).scalar_one_or_none()
    if result is None:
        return None
    return GitHubSyncData(
        last_synced_at=result.last_synced_at,
        sync_config=result.sync_config_json or {},
    )
