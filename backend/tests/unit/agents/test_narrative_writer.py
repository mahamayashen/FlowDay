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


# ---------------------------------------------------------------------------
# Instructions function — direct tests to improve mutation coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instructions_includes_analysis_date(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions output starts with the analysis date label."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert output.startswith("Analysis date: 2026-04-14")


@pytest.mark.asyncio
async def test_instructions_includes_time_analysis_data(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions output includes TIME ANALYSIS section with tracked hours."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "TIME ANALYSIS:\n  Tracked hours:" in output
    assert "6.50" in output  # total_tracked_hours
    assert "FlowDay" in output  # most_active_project


@pytest.mark.asyncio
async def test_instructions_includes_pattern_data(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions output includes DETECTED PATTERNS section."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "DETECTED PATTERNS:" in output
    assert "time-meeting" in output
    assert "PATTERN SUMMARY:" in output


@pytest.mark.asyncio
async def test_instructions_marks_unavailable_sections(
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions marks unavailable Group A sections as 'unavailable'."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    all_none = GroupAResult(
        time_analysis=None,
        meeting_analysis=None,
        code_analysis=None,
        task_analysis=None,
        errors={},
    )
    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=all_none,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    # Anchored: "\n\nXXTIME" breaks the junction, killing "unavailable" mutations.
    assert "\n\nTIME ANALYSIS: unavailable" in output
    assert "\n\nMEETING ANALYSIS: unavailable" in output
    assert "\n\nCODE ANALYSIS: unavailable" in output
    assert "\n\nTASK ANALYSIS: unavailable" in output


@pytest.mark.asyncio
async def test_instructions_includes_errors_when_present(
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions output includes ERRORS section when Group A has errors."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    result_with_errors = GroupAResult(
        time_analysis=None,
        meeting_analysis=None,
        code_analysis=None,
        task_analysis=None,
        errors={"time_analyst": "timeout"},
    )
    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=result_with_errors,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "ERRORS:" in output
    assert "timeout" in output


@pytest.mark.asyncio
async def test_instructions_no_patterns_section(
    full_group_a_result: GroupAResult,
) -> None:
    """Instructions marks patterns as 'none' when pattern list is empty."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    empty_patterns = PatternDetectorResult(patterns=[], summary="No patterns found.")
    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=empty_patterns,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "DETECTED PATTERNS: none" in output
    assert "No patterns found." in output


@pytest.mark.asyncio
async def test_instructions_time_section_field_labels(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions TIME ANALYSIS section — junction checks kill field mutations."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    # Each assert spans two adjacent f-string literals; "XX" prefix breaks junctions.
    assert "TIME ANALYSIS:\n  Tracked hours:" in output
    assert "Tracked hours: 6.50\n  Planned hours:" in output
    assert "Planned hours: 8.00\n  Utilization:" in output
    assert "Utilization: 81.2%\n  Most active project:" in output
    assert "Most active project: FlowDay\n  Avg session:" in output
    assert "Avg session: 97.5 min\n  Insights:" in output


@pytest.mark.asyncio
async def test_instructions_meeting_section_field_labels(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions MEETING ANALYSIS section — junction checks kill field mutations."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "MEETING ANALYSIS:\n  Meeting hours:" in output
    assert "Meeting hours: 2.50\n  Meeting count:" in output
    assert "Meeting count: 3\n  Avg duration:" in output
    assert "Avg duration: 0.83h\n  Focus time:" in output
    assert "Focus time: 5.50h\n  Insights:" in output


@pytest.mark.asyncio
async def test_instructions_code_section_field_labels(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions CODE ANALYSIS section — junction checks kill field mutations."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "CODE ANALYSIS:\n  Data available:" in output
    assert "Commits: 5\n  PRs:" in output
    assert "PRs: 2\n  Avg PR cycle:" in output
    assert "Most active repo: flowday-main\n  Insights:" in output


@pytest.mark.asyncio
async def test_instructions_task_section_field_labels(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions TASK ANALYSIS section — junction checks kill field mutations."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import NarrativeWriterDeps

    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "TASK ANALYSIS:\n  Total tasks:" in output
    assert "Total tasks: 12\n  Completed:" in output
    assert "Completed: 4\n  Completion rate:" in output
    assert "Completion rate: 33.3%\n  Overdue:" in output
    assert "Overdue: 2\n  Avg completion time:" in output
    assert "Priority distribution:" in output


# ---------------------------------------------------------------------------
# System prompt + decorator registration — mutation coverage
# ---------------------------------------------------------------------------


def test_narrative_writer_system_prompt_junctions() -> None:
    """System prompt junctions between adjacent string literals are intact.

    Each assertion checks the boundary between two adjacent string literals in
    the system_prompt argument. Mutmut wraps each literal with 'XX...XX', which
    breaks the concatenation at every junction — killing the mutant.
    """
    from app.agents.narrative_writer import narrative_writer

    prompt = narrative_writer._system_prompts[0]
    # Six junction checks cover all 11 adjacent-literal boundaries (mutants 2-12).
    assert "reviews. Given" in prompt
    assert "sections: 1)" in prompt
    assert "projects, 3)" in prompt
    assert "data. Be" in prompt
    assert "items. If" in prompt
    assert "absence and" in prompt


def test_narrative_writer_instructions_registered() -> None:
    """add_analysis_context is registered as an instructions handler."""
    from app.agents.narrative_writer import add_analysis_context, narrative_writer

    assert add_analysis_context in narrative_writer._instructions


@pytest.mark.asyncio
async def test_instructions_none_project_and_repo_fallback(
    sample_pattern_result: PatternDetectorResult,
) -> None:
    """Instructions renders 'none' fallback when most_active_project/repo is None."""
    from unittest.mock import MagicMock

    from app.agents.narrative_writer import add_analysis_context
    from app.agents.schemas import (
        CodeAnalystResult,
        NarrativeWriterDeps,
        TimeAnalystResult,
    )

    group_a = GroupAResult(
        time_analysis=TimeAnalystResult(
            total_tracked_hours=4.0,
            total_planned_hours=8.0,
            utilization_pct=50.0,
            most_active_project=None,
            avg_session_minutes=60.0,
            insights=[],
        ),
        meeting_analysis=None,
        code_analysis=CodeAnalystResult(
            data_available=True,
            commits_count=1,
            pull_requests_count=0,
            avg_pr_cycle_hours=0.0,
            most_active_repo=None,
            insights=[],
        ),
        task_analysis=None,
        errors={},
    )
    deps = NarrativeWriterDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=group_a,
        pattern_result=sample_pattern_result,
    )
    ctx = MagicMock()
    ctx.deps = deps

    output = await add_analysis_context(ctx)

    assert "Most active project: none" in output
    assert "Most active repo: none" in output
