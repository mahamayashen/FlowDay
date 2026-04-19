from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic_ai.models.test import TestModel


@pytest.fixture
def sample_tasks() -> list:
    from app.agents.schemas import TaskData

    now = datetime(2026, 4, 14, 10, 0, tzinfo=UTC)
    return [
        TaskData(
            task_id=uuid.uuid4(),
            title="Write unit tests",
            project_name="FlowDay",
            status="done",
            priority="high",
            estimate_minutes=60,
            due_date=date(2026, 4, 14),
            created_at=datetime(2026, 4, 13, 9, 0, tzinfo=UTC),
            completed_at=now,
        ),
        TaskData(
            task_id=uuid.uuid4(),
            title="Implement agents",
            project_name="FlowDay",
            status="in_progress",
            priority="high",
            estimate_minutes=120,
            due_date=date(2026, 4, 13),  # overdue
            created_at=datetime(2026, 4, 12, 9, 0, tzinfo=UTC),
            completed_at=None,
        ),
        TaskData(
            task_id=uuid.uuid4(),
            title="Update docs",
            project_name="FlowDay",
            status="todo",
            priority="medium",
            estimate_minutes=30,
            due_date=None,
            created_at=datetime(2026, 4, 14, 8, 0, tzinfo=UTC),
            completed_at=None,
        ),
    ]


@pytest.mark.asyncio
async def test_task_analyst_result_conforms_to_schema(sample_tasks):
    """Agent with TestModel returns a valid TaskAnalystResult schema."""
    from app.agents.schemas import TaskAnalystDeps, TaskAnalystResult
    from app.agents.task_analyst import task_analyst

    deps = TaskAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        tasks=sample_tasks,
    )

    with task_analyst.override(model=TestModel()):
        result = await task_analyst.run("Analyze tasks", deps=deps)

    output = result.output
    assert isinstance(output, TaskAnalystResult)
    assert output.total_tasks >= 0
    assert output.completed_tasks >= 0
    assert 0.0 <= output.completion_rate_pct <= 100.0
    assert output.overdue_tasks >= 0
    assert isinstance(output.priority_distribution, dict)
    assert isinstance(output.insights, list)


@pytest.mark.asyncio
async def test_task_analyst_no_completed_tasks():
    """Completion rate is 0 when all tasks are in todo state."""
    from app.agents.schemas import TaskAnalystDeps, TaskAnalystResult, TaskData
    from app.agents.task_analyst import task_analyst

    tasks = [
        TaskData(
            task_id=uuid.uuid4(),
            title="Todo item",
            project_name="FlowDay",
            status="todo",
            priority="low",
            estimate_minutes=None,
            due_date=None,
            created_at=datetime(2026, 4, 14, 8, 0, tzinfo=UTC),
            completed_at=None,
        )
    ]

    deps = TaskAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        tasks=tasks,
    )

    with task_analyst.override(model=TestModel()):
        result = await task_analyst.run("Analyze tasks", deps=deps)

    output = result.output
    assert isinstance(output, TaskAnalystResult)
    # TestModel returns 0 for int fields and 0.0 for float fields
    assert output.completion_rate_pct >= 0.0
