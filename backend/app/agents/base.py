"""Shared agent utilities: metrics-instrumented runner and DB data-fetch helpers."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from pydantic_ai import Agent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import (
    GitHubSyncData,
    ScheduleBlockData,
    TaskData,
    TimeEntryData,
)
from app.core.config import settings
from app.core.metrics import agent_latency_seconds
from app.models.external_sync import ExternalSync, SyncProvider
from app.models.project import Project
from app.models.schedule_block import ScheduleBlock
from app.models.task import Task
from app.models.time_entry import TimeEntry

log = logging.getLogger(__name__)


async def run_with_metrics[T](
    agent: Agent[Any, T],
    name: str,
    deps: Any,
) -> T:
    """Run an agent and record its wall-clock latency in Prometheus.

    When PII anonymization is enabled, deps are anonymized before the LLM call
    and the output is de-anonymized before returning.
    """
    start = time.perf_counter()
    try:
        if settings.PII_ANONYMIZATION_ENABLED:
            from app.core.anonymizer import (
                PIIAnonymizer,
                anonymize_deps,
                deanonymize_output,
            )

            anonymizer = PIIAnonymizer()
            safe_deps = anonymize_deps(deps, anonymizer)
            result = await agent.run(
                "Analyze and produce structured insights.", deps=safe_deps
            )
            output = deanonymize_output(result.output, anonymizer)
            summary = anonymizer.get_audit_summary()
            if summary:
                log.info("PII anonymized for agent=%s: %s", name, summary)
            return output
        else:
            result = await agent.run(
                "Analyze and produce structured insights.", deps=deps
            )
            return result.output
    finally:
        elapsed = time.perf_counter() - start
        agent_latency_seconds.labels(agent_name=name).observe(elapsed)


async def fetch_time_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    analysis_date: date,
) -> list[TimeEntryData]:
    """Fetch completed time entries for the given user on the analysis date."""
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


async def fetch_schedule_blocks(
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


async def fetch_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[TaskData]:
    """Fetch all tasks for the given user across all projects."""
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
            priority=(
                row.priority.value if hasattr(row.priority, "value") else row.priority
            ),
            estimate_minutes=row.estimate_minutes,
            due_date=row.due_date,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )
        for row in rows
    ]


async def fetch_github_sync(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> GitHubSyncData | None:
    """Return GitHub sync metadata for the user, or None when not configured."""
    stmt = select(ExternalSync).where(
        ExternalSync.user_id == user_id,
        ExternalSync.provider == SyncProvider.GITHUB,
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if record is None:
        return None
    return GitHubSyncData(
        last_synced_at=record.last_synced_at,
        sync_config=record.sync_config_json or {},
    )
