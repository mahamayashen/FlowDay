from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic_ai.models.test import TestModel

# CONFLICT RESOLUTION NOTE:
# Option A (chosen): top-level import + typed fixture + `-> None` annotations
# Option B (incoming): inline import inside fixture + untyped `list` + no annotations
from app.agents.schemas import ScheduleBlockData


@pytest.fixture
def sample_calendar_blocks() -> list[ScheduleBlockData]:
    return [
        ScheduleBlockData(
            task_id=uuid.uuid4(),
            task_title="Team standup",
            date=date(2026, 4, 14),
            start_hour=9.0,
            end_hour=9.5,
            source="google_calendar",
        ),
        ScheduleBlockData(
            task_id=uuid.uuid4(),
            task_title="Sprint planning",
            date=date(2026, 4, 14),
            start_hour=10.0,
            end_hour=12.0,
            source="google_calendar",
        ),
    ]


@pytest.mark.asyncio
async def test_meeting_analyst_result_conforms_to_schema(
    sample_calendar_blocks: list[ScheduleBlockData],
) -> None:
    """Agent with TestModel returns a valid MeetingAnalystResult schema."""
    from app.agents.meeting_analyst import meeting_analyst
    from app.agents.schemas import MeetingAnalystDeps, MeetingAnalystResult

    deps = MeetingAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        calendar_blocks=sample_calendar_blocks,
    )

    with meeting_analyst.override(model=TestModel()):
        result = await meeting_analyst.run("Analyze meetings", deps=deps)

    output = result.output
    assert isinstance(output, MeetingAnalystResult)
    assert output.total_meeting_hours >= 0
    assert output.meeting_count >= 0
    assert output.avg_meeting_duration_hours >= 0
    assert output.longest_meeting_hours >= 0
    assert output.focus_time_hours >= 0
    assert isinstance(output.insights, list)


@pytest.mark.asyncio
async def test_meeting_analyst_no_calendar_blocks() -> None:
    """Agent handles empty calendar blocks without error."""
    from app.agents.meeting_analyst import meeting_analyst
    from app.agents.schemas import MeetingAnalystDeps, MeetingAnalystResult

    deps = MeetingAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        calendar_blocks=[],
    )

    with meeting_analyst.override(model=TestModel()):
        result = await meeting_analyst.run("Analyze meetings", deps=deps)

    output = result.output
    assert isinstance(output, MeetingAnalystResult)
    assert output.total_meeting_hours >= 0
    assert isinstance(output.insights, list)
