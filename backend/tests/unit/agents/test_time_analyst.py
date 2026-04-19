from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic_ai.models.test import TestModel

from app.agents.schemas import ScheduleBlockData, TimeEntryData


@pytest.fixture
def sample_time_entries() -> list[TimeEntryData]:
    task_id = uuid.uuid4()
    return [
        TimeEntryData(
            task_id=task_id,
            task_title="Write tests",
            project_name="FlowDay",
            started_at=datetime(2026, 4, 14, 9, 0, tzinfo=UTC),
            ended_at=datetime(2026, 4, 14, 11, 0, tzinfo=UTC),
            duration_seconds=7200,
        ),
        TimeEntryData(
            task_id=task_id,
            task_title="Write tests",
            project_name="FlowDay",
            started_at=datetime(2026, 4, 14, 13, 0, tzinfo=UTC),
            ended_at=datetime(2026, 4, 14, 14, 0, tzinfo=UTC),
            duration_seconds=3600,
        ),
    ]


@pytest.fixture
def sample_schedule_blocks() -> list[ScheduleBlockData]:
    return [
        ScheduleBlockData(
            task_id=uuid.uuid4(),
            task_title="Write tests",
            date=date(2026, 4, 14),
            start_hour=9.0,
            end_hour=12.0,
            source="manual",
        ),
    ]


@pytest.mark.asyncio
async def test_time_analyst_result_conforms_to_schema(
    sample_time_entries: list[TimeEntryData],
    sample_schedule_blocks: list[ScheduleBlockData],
) -> None:
    """Agent with TestModel returns a valid TimeAnalystResult schema."""
    from app.agents.schemas import TimeAnalystDeps, TimeAnalystResult
    from app.agents.time_analyst import time_analyst

    deps = TimeAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        time_entries=sample_time_entries,
        schedule_blocks=sample_schedule_blocks,
    )

    with time_analyst.override(model=TestModel()):
        result = await time_analyst.run("Analyze time usage", deps=deps)

    output = result.output
    assert isinstance(output, TimeAnalystResult)
    assert output.total_tracked_hours >= 0
    assert output.total_planned_hours >= 0
    assert output.utilization_pct >= 0
    assert isinstance(output.insights, list)
    assert isinstance(output.avg_session_minutes, float)


@pytest.mark.asyncio
async def test_time_analyst_empty_time_entries() -> None:
    """Agent handles empty time entries without error."""
    from app.agents.schemas import TimeAnalystDeps, TimeAnalystResult
    from app.agents.time_analyst import time_analyst

    deps = TimeAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        time_entries=[],
        schedule_blocks=[],
    )

    with time_analyst.override(model=TestModel()):
        result = await time_analyst.run("Analyze time usage", deps=deps)

    output = result.output
    assert isinstance(output, TimeAnalystResult)
    assert output.total_tracked_hours >= 0
    assert isinstance(output.insights, list)
