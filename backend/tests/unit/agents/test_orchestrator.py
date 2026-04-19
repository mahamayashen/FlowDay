from __future__ import annotations

import uuid
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def analysis_date() -> date:
    return date(2026, 4, 14)


@pytest.fixture
def mock_db() -> AsyncMock:
    """AsyncSession mock with empty query results."""
    db = AsyncMock()
    empty_result = MagicMock()
    empty_result.all.return_value = []
    empty_result.scalars.return_value.all.return_value = []
    empty_result.scalar_one_or_none.return_value = None
    db.execute.return_value = empty_result
    return db


@pytest.mark.asyncio
async def test_run_group_a_returns_all_four_results(
    mock_db: AsyncMock, user_id: uuid.UUID, analysis_date: date
) -> None:
    """run_group_a returns GroupAResult with all four analyst outputs."""
    from app.agents import code_analyst as ca_mod
    from app.agents import meeting_analyst as ma_mod
    from app.agents import task_analyst as tk_mod
    from app.agents import time_analyst as ta_mod
    from app.agents.orchestrator import run_group_a
    from app.agents.schemas import GroupAResult

    with (
        ta_mod.time_analyst.override(model=TestModel()),
        ma_mod.meeting_analyst.override(model=TestModel()),
        ca_mod.code_analyst.override(model=TestModel()),
        tk_mod.task_analyst.override(model=TestModel()),
    ):
        result = await run_group_a(mock_db, user_id, analysis_date)

    assert isinstance(result, GroupAResult)
    assert result.time_analysis is not None
    assert result.meeting_analysis is not None
    assert result.code_analysis is not None
    assert result.task_analysis is not None
    assert result.errors == {}


@pytest.mark.asyncio
async def test_run_group_a_isolates_single_agent_failure(
    mock_db: AsyncMock, user_id: uuid.UUID, analysis_date: date
) -> None:
    """A single agent failure does not prevent the other three from succeeding."""
    import app.agents.orchestrator as orch_mod
    from app.agents import code_analyst as ca_mod
    from app.agents import meeting_analyst as ma_mod
    from app.agents import task_analyst as tk_mod
    from app.agents.orchestrator import run_group_a
    from app.agents.schemas import GroupAResult

    # Capture real _run_agent before patching to avoid recursion
    real_run_agent = orch_mod._run_agent

    async def selective_failure(agent: Agent[Any, Any], name: str, deps: Any) -> Any:
        if name == "time_analyst":
            raise RuntimeError("Simulated time_analyst failure")
        return await real_run_agent(agent, name, deps)

    with (
        ma_mod.meeting_analyst.override(model=TestModel()),
        ca_mod.code_analyst.override(model=TestModel()),
        tk_mod.task_analyst.override(model=TestModel()),
        patch("app.agents.orchestrator._run_agent", side_effect=selective_failure),
    ):
        result = await run_group_a(mock_db, user_id, analysis_date)

    assert isinstance(result, GroupAResult)
    assert result.meeting_analysis is not None
    assert result.code_analysis is not None
    assert result.task_analysis is not None
    assert result.time_analysis is None
    assert "time_analyst" in result.errors


@pytest.mark.asyncio
async def test_run_group_a_records_latency_metrics(
    mock_db: AsyncMock, user_id: uuid.UUID, analysis_date: date
) -> None:
    """run_group_a observes agent_latency_seconds for each agent."""
    from app.agents import code_analyst as ca_mod
    from app.agents import meeting_analyst as ma_mod
    from app.agents import task_analyst as tk_mod
    from app.agents import time_analyst as ta_mod
    from app.agents.orchestrator import run_group_a
    from app.core.metrics import agent_latency_seconds

    with (
        ta_mod.time_analyst.override(model=TestModel()),
        ma_mod.meeting_analyst.override(model=TestModel()),
        ca_mod.code_analyst.override(model=TestModel()),
        tk_mod.task_analyst.override(model=TestModel()),
        patch.object(
            agent_latency_seconds, "labels", wraps=agent_latency_seconds.labels
        ) as mock_labels,
    ):
        await run_group_a(mock_db, user_id, analysis_date)

    assert mock_labels.call_count == 4
    called_agent_names = {
        call.kwargs.get("agent_name") or call.args[0]
        for call in mock_labels.call_args_list
    }
    assert called_agent_names == {
        "time_analyst",
        "meeting_analyst",
        "code_analyst",
        "task_analyst",
    }
