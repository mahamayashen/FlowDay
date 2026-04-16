from __future__ import annotations

import uuid
from collections import namedtuple
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.schemas.analytics import StatusTag
from app.services.analytics_service import compute_status_tag, get_planned_vs_actual

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TASK_A = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")
TASK_B = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")
TASK_C = uuid.UUID("00000000-0000-0000-0000-cccccccccccc")

PlannedRow = namedtuple("PlannedRow", ["task_id", "title", "planned_hours"])
ActualRow = namedtuple("ActualRow", ["task_id", "title", "actual_hours"])


# ---------------------------------------------------------------------------
# compute_status_tag — deterministic tests
# ---------------------------------------------------------------------------


def test_compute_status_tag_done_exact_match() -> None:
    """100% of planned → done."""
    assert compute_status_tag(2.0, 2.0) == StatusTag.DONE


def test_compute_status_tag_done_at_threshold() -> None:
    """Exactly 90% of planned → done."""
    assert compute_status_tag(2.0, 1.8) == StatusTag.DONE


def test_compute_status_tag_done_over_planned() -> None:
    """More actual than planned → done."""
    assert compute_status_tag(2.0, 3.0) == StatusTag.DONE


def test_compute_status_tag_partial() -> None:
    """Less than 90% of planned → partial."""
    assert compute_status_tag(2.0, 1.0) == StatusTag.PARTIAL


def test_compute_status_tag_partial_just_below_threshold() -> None:
    """Just under 90% → partial."""
    assert compute_status_tag(2.0, 1.79) == StatusTag.PARTIAL


def test_compute_status_tag_skipped() -> None:
    """Planned but zero actual → skipped."""
    assert compute_status_tag(2.0, 0.0) == StatusTag.SKIPPED


def test_compute_status_tag_unplanned() -> None:
    """No plan but has actual → unplanned."""
    assert compute_status_tag(0.0, 1.5) == StatusTag.UNPLANNED


# ---------------------------------------------------------------------------
# compute_status_tag — property-based tests
# ---------------------------------------------------------------------------


@given(
    planned=st.floats(min_value=0.01, max_value=100.0),
    ratio=st.floats(min_value=0.9, max_value=10.0),
)
def test_status_tag_done_property(planned: float, ratio: float) -> None:
    """Any actual >= 90% of planned is done."""
    actual = planned * ratio
    assert compute_status_tag(planned, actual) == StatusTag.DONE


@given(
    planned=st.floats(min_value=0.01, max_value=100.0),
    ratio=st.floats(min_value=0.001, max_value=0.8999),
)
def test_status_tag_partial_property(planned: float, ratio: float) -> None:
    """Any 0 < actual < 90% of planned is partial."""
    actual = planned * ratio
    assert compute_status_tag(planned, actual) == StatusTag.PARTIAL


@given(actual=st.floats(min_value=0.01, max_value=100.0))
def test_status_tag_unplanned_property(actual: float) -> None:
    """Any actual > 0 with zero planned is unplanned."""
    assert compute_status_tag(0.0, actual) == StatusTag.UNPLANNED


# ---------------------------------------------------------------------------
# Helper to build a mock db whose execute returns planned + actual rows
# ---------------------------------------------------------------------------


def _mock_db(
    planned_rows: list[PlannedRow],
    actual_rows: list[ActualRow],
) -> AsyncMock:
    db = AsyncMock()
    planned_result = MagicMock()
    planned_result.all.return_value = planned_rows
    actual_result = MagicMock()
    actual_result.all.return_value = actual_rows
    db.execute.side_effect = [planned_result, actual_result]
    return db


# ---------------------------------------------------------------------------
# get_planned_vs_actual — unit tests
# ---------------------------------------------------------------------------

QUERY_DATE = date(2026, 5, 1)


@pytest.mark.asyncio
async def test_get_planned_vs_actual_mixed_statuses() -> None:
    """Tasks with different status tags are classified correctly."""
    db = _mock_db(
        planned_rows=[
            PlannedRow(TASK_A, "Task A", 2.0),  # will be done (actual 2.0)
            PlannedRow(TASK_B, "Task B", 3.0),  # will be skipped (no actual)
        ],
        actual_rows=[
            ActualRow(TASK_A, "Task A", 2.0),  # done
            ActualRow(TASK_C, "Task C", 1.5),  # unplanned (no plan)
        ],
    )
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    assert resp.date == QUERY_DATE
    by_id = {t.task_id: t for t in resp.tasks}
    assert by_id[TASK_A].status == StatusTag.DONE
    assert by_id[TASK_B].status == StatusTag.SKIPPED
    assert by_id[TASK_C].status == StatusTag.UNPLANNED

    assert resp.summary.total_planned_hours == pytest.approx(5.0)
    assert resp.summary.total_actual_hours == pytest.approx(3.5)
    assert resp.summary.done_count == 1
    assert resp.summary.skipped_count == 1
    assert resp.summary.unplanned_count == 1


@pytest.mark.asyncio
async def test_get_planned_vs_actual_empty_day() -> None:
    """No blocks and no entries → empty tasks, zero summary."""
    db = _mock_db([], [])
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    assert resp.tasks == []
    assert resp.summary.total_planned_hours == 0.0
    assert resp.summary.total_actual_hours == 0.0
    assert resp.summary.done_count == 0


@pytest.mark.asyncio
async def test_get_planned_vs_actual_only_planned() -> None:
    """All planned, no actuals → all skipped."""
    db = _mock_db(
        planned_rows=[
            PlannedRow(TASK_A, "Task A", 2.0),
            PlannedRow(TASK_B, "Task B", 1.0),
        ],
        actual_rows=[],
    )
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    assert all(t.status == StatusTag.SKIPPED for t in resp.tasks)
    assert resp.summary.skipped_count == 2


@pytest.mark.asyncio
async def test_get_planned_vs_actual_only_actual() -> None:
    """No plan, all actual → all unplanned."""
    db = _mock_db(
        planned_rows=[],
        actual_rows=[
            ActualRow(TASK_A, "Task A", 1.0),
            ActualRow(TASK_B, "Task B", 0.5),
        ],
    )
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    assert all(t.status == StatusTag.UNPLANNED for t in resp.tasks)
    assert resp.summary.unplanned_count == 2


@pytest.mark.asyncio
async def test_get_planned_vs_actual_partial_status() -> None:
    """Actual < 90% of planned → partial."""
    db = _mock_db(
        planned_rows=[PlannedRow(TASK_A, "Task A", 4.0)],
        actual_rows=[ActualRow(TASK_A, "Task A", 1.0)],
    )
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    assert resp.tasks[0].status == StatusTag.PARTIAL
    assert resp.summary.partial_count == 1
