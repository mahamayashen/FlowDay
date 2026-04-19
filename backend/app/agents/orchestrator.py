"""Group A orchestrator — runs four parallel analyst agents via asyncio.gather."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date
from typing import Any

from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import (
    fetch_github_sync,
    fetch_schedule_blocks,
    fetch_tasks,
    fetch_time_entries,
    run_with_metrics,
)
from app.agents.code_analyst import code_analyst
from app.agents.meeting_analyst import meeting_analyst
from app.agents.narrative_writer import narrative_writer
from app.agents.pattern_detector import pattern_detector
from app.agents.schemas import (
    CodeAnalystDeps,
    GroupAResult,
    MeetingAnalystDeps,
    NarrativeWriterDeps,
    NarrativeWriterResult,
    PatternDetectorDeps,
    PatternDetectorResult,
    TaskAnalystDeps,
    TimeAnalystDeps,
)
from app.agents.task_analyst import task_analyst
from app.agents.time_analyst import time_analyst

log = logging.getLogger(__name__)


async def _run_agent(
    agent: Agent[Any, Any],
    name: str,
    deps: Any,
) -> Any:
    """Thin wrapper kept for testability — delegates to run_with_metrics."""
    return await run_with_metrics(agent, name, deps)


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
        fetch_time_entries(db, user_id, analysis_date),
        fetch_schedule_blocks(db, user_id, analysis_date),
        fetch_tasks(db, user_id),
        fetch_github_sync(db, user_id),
    )

    time_deps = TimeAnalystDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        time_entries=time_entries,
        schedule_blocks=[b for b in schedule_blocks if b.source == "manual"],
    )
    meeting_deps = MeetingAnalystDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        calendar_blocks=[b for b in schedule_blocks if b.source == "google_calendar"],
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


async def run_group_b(
    group_a_result: GroupAResult,
    user_id: uuid.UUID,
    analysis_date: date,
) -> PatternDetectorResult:
    """Run the Pattern Detector agent (Group B) on Group A outputs.

    Args:
        group_a_result: Aggregated output from all Group A analysts.
        user_id: The user whose data was analyzed.
        analysis_date: The reference date for the analysis.

    Returns:
        PatternDetectorResult with detected cross-source patterns and summary.
    """
    deps = PatternDetectorDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        group_a_result=group_a_result,
    )
    return await run_with_metrics(pattern_detector, "pattern_detector", deps)


async def run_group_c(
    group_a_result: GroupAResult,
    pattern_result: PatternDetectorResult,
    user_id: uuid.UUID,
    analysis_date: date,
) -> NarrativeWriterResult:
    """Run the Narrative Writer agent (Group C) on Group A + B outputs.

    Args:
        group_a_result: Aggregated output from all Group A analysts.
        pattern_result: Output from the Pattern Detector (Group B).
        user_id: The user whose data was analyzed.
        analysis_date: The reference date for the analysis.

    Returns:
        NarrativeWriterResult with four narrative sections.
    """
    deps = NarrativeWriterDeps(
        user_id=user_id,
        analysis_date=analysis_date,
        group_a_result=group_a_result,
        pattern_result=pattern_result,
    )
    return await run_with_metrics(narrative_writer, "narrative_writer", deps)
