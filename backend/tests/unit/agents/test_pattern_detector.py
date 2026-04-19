from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic_ai.models.test import TestModel

from app.agents.schemas import (
    GroupAResult,
)


@pytest.mark.asyncio
async def test_pattern_detector_result_conforms_to_schema(
    full_group_a_result: GroupAResult,
) -> None:
    """Agent with TestModel returns a valid PatternDetectorResult schema."""
    from app.agents.pattern_detector import pattern_detector
    from app.agents.schemas import PatternDetectorDeps, PatternDetectorResult

    deps = PatternDetectorDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
    )

    with pattern_detector.override(model=TestModel()):
        result = await pattern_detector.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output, PatternDetectorResult)
    assert isinstance(output.patterns, list)
    assert isinstance(output.summary, str)


@pytest.mark.asyncio
async def test_pattern_detector_handles_partial_group_a(
    partial_group_a_result: GroupAResult,
) -> None:
    """Agent handles partial Group A output (some analysts failed) without error."""
    from app.agents.pattern_detector import pattern_detector
    from app.agents.schemas import PatternDetectorDeps, PatternDetectorResult

    deps = PatternDetectorDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=partial_group_a_result,
    )

    with pattern_detector.override(model=TestModel()):
        result = await pattern_detector.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output, PatternDetectorResult)
    assert isinstance(output.patterns, list)
    assert isinstance(output.summary, str)


@pytest.mark.asyncio
async def test_pattern_detector_handles_all_none_group_a() -> None:
    """Agent handles all-None Group A output (catastrophic failure) without error."""
    from app.agents.pattern_detector import pattern_detector
    from app.agents.schemas import PatternDetectorDeps, PatternDetectorResult

    all_none = GroupAResult(
        time_analysis=None,
        meeting_analysis=None,
        code_analysis=None,
        task_analysis=None,
        errors={
            "time_analyst": "timeout",
            "meeting_analyst": "timeout",
            "code_analyst": "timeout",
            "task_analyst": "timeout",
        },
    )
    deps = PatternDetectorDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=all_none,
    )

    with pattern_detector.override(model=TestModel()):
        result = await pattern_detector.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output, PatternDetectorResult)
    assert isinstance(output.patterns, list)
    assert isinstance(output.summary, str)


@pytest.mark.asyncio
async def test_pattern_detector_each_pattern_has_required_fields(
    full_group_a_result: GroupAResult,
) -> None:
    """Each CrossPattern in the output has all required fields with valid values."""
    from app.agents.pattern_detector import pattern_detector
    from app.agents.schemas import CrossPattern, PatternDetectorDeps

    deps = PatternDetectorDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
    )

    with pattern_detector.override(model=TestModel()):
        result = await pattern_detector.run(
            "Analyze and produce structured insights.", deps=deps
        )

    for p in result.output.patterns:
        assert isinstance(p, CrossPattern)
        assert isinstance(p.category, str)
        assert isinstance(p.pattern, str)
        assert 0.0 <= p.confidence <= 1.0
        assert isinstance(p.evidence, list)
        assert isinstance(p.recommendation, str)


@pytest.mark.asyncio
async def test_pattern_detector_metrics_recorded(
    full_group_a_result: GroupAResult,
) -> None:
    """run_with_metrics records latency under 'pattern_detector' label."""
    from unittest.mock import patch

    from app.agents.base import run_with_metrics
    from app.agents.pattern_detector import pattern_detector
    from app.agents.schemas import PatternDetectorDeps
    from app.core.metrics import agent_latency_seconds

    deps = PatternDetectorDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
    )

    with (
        pattern_detector.override(model=TestModel()),
        patch.object(
            agent_latency_seconds, "labels", wraps=agent_latency_seconds.labels
        ) as mock_labels,
    ):
        await run_with_metrics(pattern_detector, "pattern_detector", deps)

    mock_labels.assert_called_once_with(agent_name="pattern_detector")


@pytest.mark.asyncio
async def test_run_group_b_returns_pattern_detector_result(
    full_group_a_result: GroupAResult,
) -> None:
    """run_group_b returns a valid PatternDetectorResult."""
    import app.agents.pattern_detector as pd_mod
    from app.agents.orchestrator import run_group_b
    from app.agents.schemas import PatternDetectorResult

    with pd_mod.pattern_detector.override(model=TestModel()):
        result = await run_group_b(
            group_a_result=full_group_a_result,
            user_id=uuid.uuid4(),
            analysis_date=date(2026, 4, 14),
        )

    assert isinstance(result, PatternDetectorResult)
    assert isinstance(result.patterns, list)
    assert isinstance(result.summary, str)
