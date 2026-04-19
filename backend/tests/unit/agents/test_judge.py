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
    """Result validator raises ModelRetry when any dimension score is below threshold."""  # noqa: E501
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


# ---------------------------------------------------------------------------
# Cycle 4 — Score history DB model
# ---------------------------------------------------------------------------


def test_agent_score_history_model_has_required_fields() -> None:
    """AgentScoreHistory ORM model exposes all required columns."""
    from app.models.agent_score_history import AgentScoreHistory

    record = AgentScoreHistory(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        actionability_score=8,
        accuracy_score=9,
        coherence_score=7,
        overall_score=8,
        feedback="Good narrative.",
        retry_count=0,
    )

    assert record.user_id is not None
    assert record.analysis_date == date(2026, 4, 14)
    assert record.actionability_score == 8
    assert record.accuracy_score == 9
    assert record.coherence_score == 7
    assert record.overall_score == 8
    assert record.feedback == "Good narrative."
    assert record.retry_count == 0


def test_agent_score_history_table_name() -> None:
    """AgentScoreHistory maps to the agent_score_history table."""
    from app.models.agent_score_history import AgentScoreHistory

    assert AgentScoreHistory.__tablename__ == "agent_score_history"


# ---------------------------------------------------------------------------
# Cycle 5 — Orchestrator integration and Prometheus metrics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_group_d_returns_judge_result(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """run_group_d returns a valid JudgeResult."""
    import app.agents.judge as judge_mod
    from app.agents.orchestrator import run_group_d
    from app.agents.schemas import JudgeResult

    with judge_mod.judge.override(model=_make_passing_model()):
        result = await run_group_d(
            group_a_result=full_group_a_result,
            pattern_result=sample_pattern_result,
            narrative_result=sample_narrative_result,
            user_id=uuid.uuid4(),
            analysis_date=date(2026, 4, 14),
        )

    assert isinstance(result, JudgeResult)
    assert isinstance(result.feedback, str)
    assert len(result.feedback) > 0


@pytest.mark.asyncio
async def test_run_group_d_records_judge_score_metric(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """run_group_d observes the overall_score in the judge_score histogram."""
    from unittest.mock import MagicMock, patch

    import app.agents.judge as judge_mod
    from app.agents.orchestrator import run_group_d
    from app.core.metrics import judge_score

    mock_histogram = MagicMock()
    with (
        judge_mod.judge.override(model=_make_passing_model()),
        patch.object(judge_score, "labels", return_value=mock_histogram) as mock_labels,
    ):
        result = await run_group_d(
            group_a_result=full_group_a_result,
            pattern_result=sample_pattern_result,
            narrative_result=sample_narrative_result,
            user_id=uuid.uuid4(),
            analysis_date=date(2026, 4, 14),
        )

    mock_labels.assert_called_once_with(agent_name="judge")
    mock_histogram.observe.assert_called_once_with(result.overall_score)


def test_judge_retry_count_metric_exists() -> None:
    """judge_retry_count Counter is defined in metrics module."""
    from prometheus_client import Counter

    from app.core.metrics import judge_retry_count

    assert isinstance(judge_retry_count, Counter)


# ---------------------------------------------------------------------------
# Mutation killers — prompt content and agent configuration
# ---------------------------------------------------------------------------


def test_judge_max_retries_is_two() -> None:
    """Judge agent is configured with exactly 2 retries (max_result_retries)."""
    from app.agents.judge import judge

    assert judge._max_result_retries == 2


def test_judge_system_prompt_covers_all_dimensions() -> None:
    """System prompt references all three scoring dimensions and overall score."""
    from app.agents.judge import judge

    prompt = " ".join(judge._system_prompts)
    assert "actionability_score" in prompt
    assert "accuracy_score" in prompt
    assert "coherence_score" in prompt
    assert "overall_score" in prompt
    assert "You are an impartial evaluator" in prompt
    assert "1\u201310" in prompt or "1-10" in prompt  # en-dash or hyphen variant
    assert "XX" not in prompt


@pytest.mark.asyncio
async def test_serialize_group_a_summary_includes_time_data(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """_serialize_group_a_summary includes tracked hours and utilization."""
    from app.agents.judge import _serialize_group_a_summary
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    lines = _serialize_group_a_summary(deps)
    combined = "\n".join(lines)

    assert any(line.startswith("TIME: tracked") for line in lines)
    assert "6.50h" in combined
    assert "81.2%" in combined
    assert "XX" not in combined


@pytest.mark.asyncio
async def test_serialize_group_a_summary_includes_meeting_data(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """_serialize_group_a_summary includes meeting count and focus hours."""
    from app.agents.judge import _serialize_group_a_summary
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    lines = _serialize_group_a_summary(deps)
    combined = "\n".join(lines)

    assert any(line.startswith("MEETINGS: 3 meetings") for line in lines)
    assert "focus=5.50h" in combined
    assert "XX" not in combined


@pytest.mark.asyncio
async def test_serialize_group_a_summary_pattern_line_format(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """Pattern lines include category, pattern text, and confidence value."""
    from app.agents.judge import _serialize_group_a_summary
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    lines = _serialize_group_a_summary(deps)
    combined = "\n".join(lines)

    assert "  - [time-meeting]" in combined
    assert "confidence=0.85" in combined
    assert "PATTERNS:\n  - [time-meeting]" in combined
    assert "XX" not in combined


@pytest.mark.asyncio
async def test_serialize_group_a_summary_includes_code_and_task_data(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """_serialize_group_a_summary includes commit/PR counts and task completion."""
    from app.agents.judge import _serialize_group_a_summary
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    lines = _serialize_group_a_summary(deps)
    combined = "\n".join(lines)

    assert any(line.startswith("CODE: commits=5") for line in lines)
    assert "prs=2" in combined
    assert "4/12" in combined
    assert any(line.startswith("PATTERNS:") for line in lines)
    assert "XX" not in combined


@pytest.mark.asyncio
async def test_serialize_group_a_summary_unavailable_sections(
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """_serialize_group_a_summary marks missing sections as unavailable."""
    from app.agents.judge import _serialize_group_a_summary
    from app.agents.schemas import JudgeDeps

    empty_ga = GroupAResult(
        time_analysis=None,
        meeting_analysis=None,
        code_analysis=None,
        task_analysis=None,
        errors={},
    )
    empty_pattern = PatternDetectorResult(patterns=[], summary="No patterns.")
    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=empty_ga,
        pattern_result=empty_pattern,
        narrative_result=sample_narrative_result,
    )

    lines = _serialize_group_a_summary(deps)
    combined = "\n".join(lines)

    assert any(line == "TIME: unavailable" for line in lines)
    assert any(line == "MEETINGS: unavailable" for line in lines)
    assert any(line == "CODE: unavailable" for line in lines)
    assert any(line == "TASKS: unavailable" for line in lines)
    assert any(line == "PATTERNS: none detected" for line in lines)
    assert "XX" not in combined


@pytest.mark.asyncio
async def test_add_evaluation_context_contains_narrative_sections(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """add_evaluation_context output contains analysis_date and narrative content."""
    import app.agents.judge as judge_mod
    from app.agents.schemas import JudgeDeps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )

    # Create a fake RunContext-like object
    class FakeCtx:
        def __init__(self, deps):  # type: ignore[no-untyped-def]
            self.deps = deps

    ctx = FakeCtx(deps)
    context_str = await judge_mod.add_evaluation_context(ctx)  # type: ignore[arg-type]

    assert "Analysis date: 2026-04-14" in context_str
    assert "--- NARRATIVE TO EVALUATE ---" in context_str
    assert sample_narrative_result.executive_summary in context_str
    assert "--- UNDERLYING DATA ---" in context_str
    assert context_str.count("\n\n") >= 3  # sections joined by double newline
    assert "XX" not in context_str


@pytest.mark.asyncio
async def test_validate_scores_exact_threshold_boundary(
    full_group_a_result: GroupAResult,
    sample_pattern_result: PatternDetectorResult,
    sample_narrative_result: NarrativeWriterResult,
) -> None:
    """Score exactly at threshold does not trigger retry; one below does."""
    from pydantic_ai import ModelRetry

    from app.agents.judge import validate_scores
    from app.agents.schemas import JudgeDeps, JudgeResult
    from app.core.config import settings

    class FakeCtx:
        def __init__(self, deps):  # type: ignore[no-untyped-def]
            self.deps = deps

    deps = JudgeDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        group_a_result=full_group_a_result,
        pattern_result=sample_pattern_result,
        narrative_result=sample_narrative_result,
    )
    ctx = FakeCtx(deps)
    threshold = settings.JUDGE_SCORE_THRESHOLD

    # Exactly at threshold — no retry
    at_threshold = JudgeResult(
        actionability_score=threshold,
        accuracy_score=threshold,
        coherence_score=threshold,
        overall_score=threshold,
        feedback="Meets threshold.",
    )
    result = await validate_scores(ctx, at_threshold)  # type: ignore[arg-type]
    assert result is at_threshold

    # One below threshold — raises ModelRetry
    below = JudgeResult(
        actionability_score=threshold - 1,
        accuracy_score=threshold,
        coherence_score=threshold,
        overall_score=threshold - 1,
        feedback="Below threshold.",
    )
    with pytest.raises(ModelRetry):
        await validate_scores(ctx, below)  # type: ignore[arg-type]


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
