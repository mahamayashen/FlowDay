"""Unit tests for the Judge agent (Group D)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.agents.schemas import (
    GroupAResult,
    NarrativeWriterResult,
    PatternDetectorResult,
)


def _make_passing_model():  # type: ignore[return]
    """Return a FunctionModel that always emits scores above the retry threshold."""
    from pydantic_ai.models.function import FunctionModel

    from app.agents.schemas import JudgeResult

    def _model(messages, info):  # type: ignore[return, type-arg]
        from pydantic_ai.models.function import ModelResponse, TextPart

        result = JudgeResult(
            actionability_score=8,
            accuracy_score=9,
            coherence_score=7,
            overall_score=8,
            feedback="Well-grounded narrative with actionable observations.",
        )
        return ModelResponse(parts=[TextPart(result.model_dump_json())])

    return FunctionModel(_model)


# ---------------------------------------------------------------------------
# Cycle 1 — Schema + basic agent output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_judge_result_conforms_to_schema(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """Agent returns a valid JudgeResult schema."""
    from app.agents.judge import judge
    from app.agents.schemas import JudgeDeps, JudgeResult

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    with judge.override(model=_make_passing_model()):
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

    with judge.override(model=_make_passing_model()):
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

    with judge.override(model=_make_passing_model()):
        result = await judge.run("Analyze and produce structured insights.", deps=deps)

    assert isinstance(result.output.feedback, str)
    assert len(result.output.feedback) > 0


# ---------------------------------------------------------------------------
# Cycle 2 — ModelRetry on low scores
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_judge_raises_model_retry_when_score_below_threshold(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """Result validator raises ModelRetry when any dimension score is below threshold."""
    from pydantic_ai import ModelRetry
    from pydantic_ai.models.function import AgentInfo, FunctionModel

    from app.agents.judge import judge
    from app.agents.schemas import JudgeDeps, JudgeResult

    def low_score_model(messages: list, info: AgentInfo) -> object:  # type: ignore[type-arg]
        from pydantic_ai.models.function import ModelResponse, TextPart

        # Return scores all at 3 — below the default threshold of 6
        result = JudgeResult(
            actionability_score=3,
            accuracy_score=3,
            coherence_score=3,
            overall_score=3,
            feedback="Weak narrative.",
        )
        return ModelResponse(parts=[TextPart(result.model_dump_json())])

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    with pytest.raises(Exception):  # MaxRetriesExceeded after retries=2
        with judge.override(model=FunctionModel(low_score_model)):
            await judge.run("Analyze and produce structured insights.", deps=deps)


@pytest.mark.asyncio
async def test_judge_no_retry_when_all_scores_above_threshold(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """No retry is triggered when all dimension scores meet the threshold."""
    from pydantic_ai.models.function import AgentInfo, FunctionModel

    from app.agents.judge import judge
    from app.agents.schemas import JudgeDeps, JudgeResult

    def good_score_model(messages: list, info: AgentInfo) -> object:  # type: ignore[type-arg]
        from pydantic_ai.models.function import ModelResponse, TextPart

        result = JudgeResult(
            actionability_score=8,
            accuracy_score=9,
            coherence_score=7,
            overall_score=8,
            feedback="Strong narrative with clear grounding.",
        )
        return ModelResponse(parts=[TextPart(result.model_dump_json())])

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    with judge.override(model=FunctionModel(good_score_model)):
        result = await judge.run("Analyze and produce structured insights.", deps=deps)

    assert result.output.actionability_score >= 6
    assert result.output.accuracy_score >= 6
    assert result.output.coherence_score >= 6


# ---------------------------------------------------------------------------
# Cycle 3 — Provider isolation
# ---------------------------------------------------------------------------


def test_judge_uses_different_model_than_narrative_writer() -> None:
    """Judge agent's configured model differs from the Narrative Writer's model."""
    from app.agents.judge import judge
    from app.agents.narrative_writer import narrative_writer

    judge_model = str(judge.model)
    writer_model = str(narrative_writer.model)
    assert judge_model != writer_model, (
        f"Judge and Narrative Writer must use different providers, "
        f"but both use: {judge_model}"
    )


def test_judge_model_is_llm_judge_model_setting() -> None:
    """Judge agent is configured with settings.LLM_JUDGE_MODEL."""
    from app.agents.judge import judge
    from app.core.config import settings

    assert settings.LLM_JUDGE_MODEL in str(judge.model)


def test_narrative_writer_model_is_llm_model_setting() -> None:
    """Narrative Writer is configured with settings.LLM_MODEL (not the judge model)."""
    from app.agents.narrative_writer import narrative_writer
    from app.core.config import settings

    assert settings.LLM_MODEL in str(narrative_writer.model)


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
