"""Unit tests for the Judge agent (Group D)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic_ai.models.test import TestModel

from app.agents.schemas import (
    GroupAResult,
    NarrativeWriterResult,
    PatternDetectorResult,
)

# ---------------------------------------------------------------------------
# Cycle 1 — Schema + basic agent output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_judge_result_conforms_to_schema(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """Agent with TestModel returns a valid JudgeResult schema."""
    from app.agents.judge import judge
    from app.agents.schemas import JudgeDeps, JudgeResult

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    with judge.override(model=TestModel()):
        result = await judge.run("Analyze and produce structured insights.", deps=deps)

    output = result.output
    assert isinstance(output, JudgeResult)
    assert hasattr(output, "actionability_score")
    assert hasattr(output, "accuracy_score")
    assert hasattr(output, "coherence_score")
    assert hasattr(output, "overall_score")
    assert hasattr(output, "feedback")


@pytest.mark.asyncio
async def test_judge_all_scores_within_range(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """All four scores are integers in the range [1, 10]."""
    from app.agents.judge import judge
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    with judge.override(model=TestModel()):
        result = await judge.run("Analyze and produce structured insights.", deps=deps)

    output = result.output
    for score in (
        output.actionability_score,
        output.accuracy_score,
        output.coherence_score,
        output.overall_score,
    ):
        assert isinstance(score, int)
        assert 1 <= score <= 10


@pytest.mark.asyncio
async def test_judge_feedback_is_non_empty_string(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """Feedback field is a non-empty string."""
    from app.agents.judge import judge
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    with judge.override(model=TestModel()):
        result = await judge.run("Analyze and produce structured insights.", deps=deps)

    assert isinstance(result.output.feedback, str)
    assert len(result.output.feedback) > 0


def test_judge_deps_accepts_full_pipeline_inputs(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """JudgeDeps can be constructed without errors from full pipeline outputs."""
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    assert deps.user_id is not None
    assert deps.analysis_date == date(2026, 4, 14)
    assert deps.group_a_result is full_group_a_result
    assert deps.pattern_result is sample_pattern_result
    assert deps.narrative_result is sample_narrative_result
