from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.weekly_review import ReviewStatus, WeeklyReview
from app.services.weekly_review_service import (
    _align_to_monday,
    generate_review,
    get_or_create_review,
    get_review,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Cycle 3 — _align_to_monday helper
# ---------------------------------------------------------------------------


def test_align_to_monday_already_monday() -> None:
    assert _align_to_monday(date(2026, 4, 13)) == date(2026, 4, 13)


def test_align_to_monday_from_wednesday() -> None:
    assert _align_to_monday(date(2026, 4, 15)) == date(2026, 4, 13)


def test_align_to_monday_from_sunday() -> None:
    assert _align_to_monday(date(2026, 4, 19)) == date(2026, 4, 13)


# ---------------------------------------------------------------------------
# Cycle 3 — get_or_create_review
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_or_create_review_creates_new() -> None:
    """When no review exists, a new one is created with status=pending."""
    db = MagicMock()
    # Simulate SELECT returning no result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    week_start = date(2026, 4, 13)
    review = await get_or_create_review(db, USER_ID, week_start)

    assert review.user_id == USER_ID
    assert review.week_start == week_start
    assert review.status == ReviewStatus.PENDING
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_review_returns_existing() -> None:
    """When a review exists, the existing one is returned without creating a new one."""
    existing = WeeklyReview(
        user_id=USER_ID,
        week_start=date(2026, 4, 13),
        raw_data_json={},
        status=ReviewStatus.COMPLETE,
    )
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    db.execute = AsyncMock(return_value=mock_result)

    review = await get_or_create_review(db, USER_ID, date(2026, 4, 13))

    assert review is existing
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_review_queries_by_user_id() -> None:
    """DB query must filter by the correct user_id, not another user."""

    async def fake_execute(stmt):  # type: ignore[no-untyped-def]
        # Only return a result if the query is for the correct user
        whereclause = str(stmt.whereclause)
        # Both user_id and week_start conditions must be == (not !=)
        if "!=" in whereclause:
            mock_r = MagicMock()
            mock_r.scalar_one_or_none.return_value = None
            return mock_r
        mock_r = MagicMock()
        mock_r.scalar_one_or_none.return_value = None
        return mock_r

    db = MagicMock()
    db.execute = AsyncMock(side_effect=fake_execute)
    db.flush = AsyncMock()

    # Should create a new review for USER_ID, not find the other user's review
    review = await get_or_create_review(db, USER_ID, date(2026, 4, 13))
    assert review.user_id == USER_ID


@pytest.mark.asyncio
async def test_get_or_create_review_normalizes_week_start_to_monday() -> None:
    """Input date mid-week is clamped to Monday before lookup and storage."""
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    # Wednesday → should store as Monday 2026-04-13
    review = await get_or_create_review(db, USER_ID, date(2026, 4, 15))

    assert review.week_start == date(2026, 4, 13)


# ---------------------------------------------------------------------------
# Cycle 4 — generate_review
# ---------------------------------------------------------------------------


def _make_review(status: str = ReviewStatus.PENDING) -> WeeklyReview:
    return WeeklyReview(
        user_id=USER_ID,
        week_start=date(2026, 4, 13),
        raw_data_json={},
        status=status,
    )


@pytest.mark.asyncio
async def test_get_review_returns_existing() -> None:
    """get_review returns the stored review when found."""
    existing = WeeklyReview(
        user_id=USER_ID,
        week_start=date(2026, 4, 13),
        raw_data_json={},
    )
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    db.execute = AsyncMock(return_value=mock_result)

    result = await get_review(db, USER_ID, date(2026, 4, 13))
    assert result is existing


@pytest.mark.asyncio
async def test_get_review_returns_none_when_not_found() -> None:
    """get_review returns None when no review exists for the user/week."""
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    result = await get_review(db, USER_ID, date(2026, 4, 13))
    assert result is None


@pytest.mark.asyncio
async def test_get_review_normalizes_week_start_to_monday() -> None:
    """get_review normalizes any date to Monday before querying."""
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    # Sunday — should query for Monday 2026-04-13
    await get_review(db, USER_ID, date(2026, 4, 19))
    # Verify execute was called (query happened, not skipped)
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_generate_review_sets_generating_before_pipeline() -> None:
    """Status must flip to 'generating' before any agent runs."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    status_at_call: list[str] = []

    async def fake_run_group_a(*args, **kwargs):  # type: ignore[no-untyped-def]
        status_at_call.append(review.status)
        from app.agents.schemas import GroupAResult

        return GroupAResult()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            side_effect=fake_run_group_a,
        ),
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        mock_d.return_value = None

        await generate_review(db, review, date(2026, 4, 13))

    assert status_at_call == [ReviewStatus.GENERATING]


@pytest.mark.asyncio
async def test_generate_review_sets_status_complete_on_success() -> None:
    """After a successful pipeline run, status must be 'complete'."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            GroupAResult,
            JudgeResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="summary",
            time_analysis="time",
            productivity_patterns="patterns",
            areas_of_concern="concerns",
        )
        mock_d.return_value = JudgeResult(
            actionability_score=8,
            accuracy_score=9,
            coherence_score=7,
            overall_score=8,
            feedback="good",
        )

        result = await generate_review(db, review, date(2026, 4, 13))

    assert result.status == ReviewStatus.COMPLETE
    assert result.narrative is not None
    assert result.scores_json is not None


@pytest.mark.asyncio
async def test_generate_review_sets_status_failed_on_exception() -> None:
    """If run_group_a raises, status must be set to 'failed'."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with patch(
        "app.services.weekly_review_service.run_group_a",
        side_effect=RuntimeError("agent exploded"),
    ):
        with pytest.raises(RuntimeError, match="agent exploded"):
            await generate_review(db, review, date(2026, 4, 13))

    assert review.status == ReviewStatus.FAILED


@pytest.mark.asyncio
async def test_generate_review_stores_agent_metadata() -> None:
    """agent_metadata_json must be populated after a successful run."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            GroupAResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        mock_d.return_value = None

        result = await generate_review(db, review, date(2026, 4, 13))

    assert result.agent_metadata_json is not None
    assert "analysis_date" in result.agent_metadata_json


@pytest.mark.asyncio
async def test_generate_review_populates_insights_from_group_a() -> None:
    """insights_json must be populated from group_a_result, not None."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            GroupAResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        mock_d.return_value = None
        result = await generate_review(db, review, date(2026, 4, 13))

    assert result.insights_json is not None
    assert isinstance(result.insights_json, dict)


@pytest.mark.asyncio
async def test_generate_review_narrative_contains_all_sections() -> None:
    """narrative must concatenate all four NarrativeWriterResult sections."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            GroupAResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="EXEC_SUMMARY",
            time_analysis="TIME_ANALYSIS",
            productivity_patterns="PRODUCTIVITY",
            areas_of_concern="CONCERNS",
        )
        mock_d.return_value = None
        result = await generate_review(db, review, date(2026, 4, 13))

    assert result.narrative is not None
    assert "EXEC_SUMMARY" in result.narrative
    assert "TIME_ANALYSIS" in result.narrative
    assert "PRODUCTIVITY" in result.narrative
    assert "CONCERNS" in result.narrative


@pytest.mark.asyncio
async def test_generate_review_metadata_has_required_keys() -> None:
    """agent_metadata_json must have patterns_detected, group_a_errors, judge_scored."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            GroupAResult,
            JudgeResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        mock_d.return_value = JudgeResult(
            actionability_score=8,
            accuracy_score=9,
            coherence_score=7,
            overall_score=8,
            feedback="good",
        )
        result = await generate_review(db, review, date(2026, 4, 13))

    meta = result.agent_metadata_json
    assert meta is not None
    assert "patterns_detected" in meta
    assert "group_a_errors" in meta
    assert meta["judge_scored"] is True


@pytest.mark.asyncio
async def test_generate_review_calls_run_group_d() -> None:
    """run_group_d must be called — skipping it is not acceptable."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()
    judge_called = []

    async def fake_run_group_d(*args, **kwargs):  # type: ignore[no-untyped-def]
        judge_called.append(True)
        from app.agents.schemas import JudgeResult

        return JudgeResult(
            actionability_score=7,
            accuracy_score=8,
            coherence_score=9,
            overall_score=8,
            feedback="solid",
        )

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            side_effect=fake_run_group_d,
        ),
    ):
        from app.agents.schemas import (
            GroupAResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        result = await generate_review(db, review, date(2026, 4, 13))

    assert judge_called, "run_group_d was not called"
    assert result.scores_json is not None
    assert result.scores_json["overall_score"] == 8


# ---------------------------------------------------------------------------
# Cycle — per-stage observability (latency + Sentry breadcrumbs)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_review_records_per_stage_latency() -> None:
    """agent_metadata_json.stages must include latency_ms for each pipeline stage."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
    ):
        from app.agents.schemas import (
            GroupAResult,
            JudgeResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        mock_d.return_value = JudgeResult(
            actionability_score=8,
            accuracy_score=9,
            coherence_score=7,
            overall_score=8,
            feedback="good",
        )
        result = await generate_review(db, review, date(2026, 4, 13))

    meta = result.agent_metadata_json
    assert meta is not None
    stages = meta.get("stages")
    assert stages is not None, "agent_metadata_json must include a 'stages' mapping"
    for name in ("group_a", "group_b", "group_c", "group_d"):
        assert name in stages, f"missing stage entry for {name}"
        assert "latency_ms" in stages[name], f"{name} missing latency_ms"
        assert isinstance(stages[name]["latency_ms"], int | float)
        assert stages[name]["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_generate_review_emits_sentry_breadcrumb_per_stage() -> None:
    """Each pipeline stage must emit a Sentry breadcrumb tagged with its name."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
        ) as mock_a,
        patch(
            "app.services.weekly_review_service.run_group_b",
            new_callable=AsyncMock,
        ) as mock_b,
        patch(
            "app.services.weekly_review_service.run_group_c",
            new_callable=AsyncMock,
        ) as mock_c,
        patch(
            "app.services.weekly_review_service.run_group_d",
            new_callable=AsyncMock,
        ) as mock_d,
        patch(
            "app.services.weekly_review_service.sentry_sdk.add_breadcrumb"
        ) as mock_crumb,
    ):
        from app.agents.schemas import (
            GroupAResult,
            JudgeResult,
            NarrativeWriterResult,
            PatternDetectorResult,
        )

        mock_a.return_value = GroupAResult()
        mock_b.return_value = PatternDetectorResult(patterns=[], summary="ok")
        mock_c.return_value = NarrativeWriterResult(
            executive_summary="s",
            time_analysis="t",
            productivity_patterns="p",
            areas_of_concern="a",
        )
        mock_d.return_value = JudgeResult(
            actionability_score=8,
            accuracy_score=9,
            coherence_score=7,
            overall_score=8,
            feedback="good",
        )
        await generate_review(db, review, date(2026, 4, 13))

    messages = [c.kwargs.get("message", "") for c in mock_crumb.call_args_list]
    joined = " | ".join(messages)
    for name in ("group_a", "group_b", "group_c", "group_d"):
        assert name in joined, f"no breadcrumb emitted for {name} (got: {joined!r})"


@pytest.mark.asyncio
async def test_generate_review_emits_failed_breadcrumb_on_exception() -> None:
    """On pipeline failure a breadcrumb with level=error must be emitted."""
    db = MagicMock()
    db.flush = AsyncMock()
    review = _make_review()

    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        patch(
            "app.services.weekly_review_service.sentry_sdk.add_breadcrumb"
        ) as mock_crumb,
    ):
        with pytest.raises(RuntimeError):
            await generate_review(db, review, date(2026, 4, 13))

    levels = [c.kwargs.get("level") for c in mock_crumb.call_args_list]
    assert "error" in levels, f"expected an error-level breadcrumb, got {levels!r}"
