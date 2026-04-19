"""Unit tests for the Narrative Writer agent (Group C)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic_ai.models.test import TestModel

from app.agents.schemas import (
    GroupAResult,
    PatternDetectorResult,
)

# ---------------------------------------------------------------------------
# Cycle 1 — Schema + basic agent output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_narrative_writer_result_conforms_to_schema(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Agent with TestModel returns a valid NarrativeWriterResult schema."""
    from app.agents.narrative_writer import narrative_writer
    from app.agents.schemas import NarrativeWriterDeps, NarrativeWriterResult

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )

    with narrative_writer.override(model=TestModel()):
        result = await narrative_writer.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output, NarrativeWriterResult)
    assert hasattr(output, "executive_summary")
    assert hasattr(output, "time_analysis")
    assert hasattr(output, "productivity_patterns")
    assert hasattr(output, "areas_of_concern")


@pytest.mark.asyncio
async def test_narrative_writer_all_sections_non_empty(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """All four narrative sections are non-empty strings."""
    from app.agents.narrative_writer import narrative_writer
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )

    with narrative_writer.override(model=TestModel()):
        result = await narrative_writer.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert len(output.executive_summary) > 0
    assert len(output.time_analysis) > 0
    assert len(output.productivity_patterns) > 0
    assert len(output.areas_of_concern) > 0


# ---------------------------------------------------------------------------
# Cycle 2 — Partial input + metrics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_narrative_writer_handles_partial_group_a(
    partial_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Agent handles partial Group A output (some analysts failed) without error."""
    from app.agents.narrative_writer import narrative_writer
    from app.agents.schemas import NarrativeWriterDeps, NarrativeWriterResult

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=partial_group_a_result,
        pattern_result=sample_pattern_result,
    )

    with narrative_writer.override(model=TestModel()):
        result = await narrative_writer.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output, NarrativeWriterResult)
    assert len(output.executive_summary) > 0
    assert len(output.time_analysis) > 0
    assert len(output.productivity_patterns) > 0
    assert len(output.areas_of_concern) > 0


@pytest.mark.asyncio
async def test_narrative_writer_handles_all_none_group_a(
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Agent handles all-None Group A output (catastrophic failure) without error."""
    from app.agents.narrative_writer import narrative_writer
    from app.agents.schemas import NarrativeWriterDeps, NarrativeWriterResult

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
    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=all_none,
        pattern_result=sample_pattern_result,
    )

    with narrative_writer.override(model=TestModel()):
        result = await narrative_writer.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output, NarrativeWriterResult)
    assert len(output.executive_summary) > 0
    assert len(output.time_analysis) > 0
    assert len(output.productivity_patterns) > 0
    assert len(output.areas_of_concern) > 0


@pytest.mark.asyncio
async def test_narrative_writer_each_section_is_string_type(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Each of the four output sections is a str instance."""
    from app.agents.narrative_writer import narrative_writer
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )

    with narrative_writer.override(model=TestModel()):
        result = await narrative_writer.run(
            "Analyze and produce structured insights.", deps=deps
        )

    output = result.output
    assert isinstance(output.executive_summary, str)
    assert isinstance(output.time_analysis, str)
    assert isinstance(output.productivity_patterns, str)
    assert isinstance(output.areas_of_concern, str)


@pytest.mark.asyncio
async def test_narrative_writer_metrics_recorded(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """run_with_metrics records latency under 'narrative_writer' label."""
    from unittest.mock import patch

    from app.agents.base import run_with_metrics
    from app.agents.narrative_writer import narrative_writer
    from app.agents.schemas import NarrativeWriterDeps
    from app.core.metrics import agent_latency_seconds

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )

    with (
        narrative_writer.override(model=TestModel()),
        patch.object(
            agent_latency_seconds, "labels", wraps=agent_latency_seconds.labels
        ) as mock_labels,
    ):
        await run_with_metrics(narrative_writer, "narrative_writer", deps)

    mock_labels.assert_called_once_with(agent_name="narrative_writer")


# ---------------------------------------------------------------------------
# Cycle 3 — Orchestrator integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_group_c_returns_narrative_writer_result(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """run_group_c returns a valid NarrativeWriterResult."""
    import app.agents.narrative_writer as nw_mod
    from app.agents.orchestrator import run_group_c
    from app.agents.schemas import NarrativeWriterResult

    with nw_mod.narrative_writer.override(model=TestModel()):
        result = await run_group_c(
            group_a_result=full_group_a_result,
            pattern_result=sample_pattern_result,
            user_id=uuid.uuid4(),
            analysis_date=date(2026, 4, 14),
        )

    assert isinstance(result, NarrativeWriterResult)
    assert isinstance(result.executive_summary, str)
    assert isinstance(result.time_analysis, str)
    assert isinstance(result.productivity_patterns, str)
    assert isinstance(result.areas_of_concern, str)
