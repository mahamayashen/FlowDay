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


# ---------------------------------------------------------------------------
# compute_status_tag — edge case
# ---------------------------------------------------------------------------


def test_compute_status_tag_zero_zero() -> None:
    """No planned and no actual → skipped (defensive)."""
    assert compute_status_tag(0.0, 0.0) == StatusTag.SKIPPED


# ---------------------------------------------------------------------------
# get_planned_vs_actual — SQL query inspection tests
# ---------------------------------------------------------------------------


def _compile(stmt: object) -> str:
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_planned_query_joins_and_filters() -> None:
    """Planned query must JOIN Task→Project and filter by date + user_id."""
    db = _mock_db([], [])
    await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    planned_stmt = db.execute.call_args_list[0][0][0]
    compiled = _compile(planned_stmt)

    # JOIN conditions use equality
    assert "schedule_blocks.task_id = tasks.id" in compiled.lower()
    assert "tasks.project_id = projects.id" in compiled.lower()
    assert "!=" not in compiled

    # WHERE filters
    assert "2026-05-01" in compiled
    assert USER_ID.hex in compiled

    # SUM uses subtraction (end_hour - start_hour)
    assert " - " in compiled


@pytest.mark.asyncio
async def test_actual_query_joins_and_filters() -> None:
    """Actual query must JOIN Task→Project and filter by date range + user_id."""
    db = _mock_db([], [])
    await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    actual_stmt = db.execute.call_args_list[1][0][0]
    compiled = _compile(actual_stmt)

    # JOIN conditions use equality
    assert "time_entries.task_id = tasks.id" in compiled.lower()
    assert "tasks.project_id = projects.id" in compiled.lower()
    assert "!=" not in compiled

    # WHERE filters: date boundaries
    assert "2026-05-01" in compiled
    assert "2026-05-02" in compiled

    # user_id filter
    assert USER_ID.hex in compiled

    # Division by 3600
    assert "3600" in compiled


@pytest.mark.asyncio
async def test_actual_query_date_boundary_operators() -> None:
    """Actual query must use >= for day_start and < for day_end."""
    db = _mock_db([], [])
    await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    actual_stmt = db.execute.call_args_list[1][0][0]
    compiled = _compile(actual_stmt)

    # Must have >= for start and < (not <=) for end
    assert ">=" in compiled
    # Check that day_end uses < not <=
    assert "< '2026-05-02" in compiled
    assert "<= '2026-05-02" not in compiled


@pytest.mark.asyncio
async def test_planned_query_uses_subtraction_not_addition() -> None:
    """Planned hours must be computed as end_hour - start_hour, not +."""
    db = _mock_db([], [])
    await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    planned_stmt = db.execute.call_args_list[0][0][0]
    compiled = _compile(planned_stmt)

    # Find the SUM expression — it should contain minus, not plus
    assert "end_hour - " in compiled.lower() or "end_hour -" in compiled.lower()
    # Make sure it's not addition
    assert "end_hour +" not in compiled.lower()
    assert "end_hour+" not in compiled.lower()


@pytest.mark.asyncio
async def test_actual_query_division_value() -> None:
    """Duration must be divided by 3600.0, not multiplied or other value."""
    db = _mock_db([], [])
    await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    actual_stmt = db.execute.call_args_list[1][0][0]
    compiled = _compile(actual_stmt)

    # Must use division, not multiplication
    assert "/ CAST(3600" in compiled or "/ 3600" in compiled
    # Must not use multiplication
    assert "* CAST(3600" not in compiled and "* 3600" not in compiled


@pytest.mark.asyncio
async def test_get_planned_vs_actual_task_titles() -> None:
    """Task titles from planned and actual maps are correctly assigned."""
    db = _mock_db(
        planned_rows=[PlannedRow(TASK_A, "Planned Title", 2.0)],
        actual_rows=[ActualRow(TASK_B, "Actual Title", 1.0)],
    )
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    by_id = {t.task_id: t for t in resp.tasks}
    assert by_id[TASK_A].task_title == "Planned Title"
    assert by_id[TASK_B].task_title == "Actual Title"


@pytest.mark.asyncio
async def test_get_planned_vs_actual_hours_values() -> None:
    """Planned and actual hours are correctly assigned to each task."""
    db = _mock_db(
        planned_rows=[PlannedRow(TASK_A, "Task A", 3.5)],
        actual_rows=[
            ActualRow(TASK_A, "Task A", 2.0),
            ActualRow(TASK_B, "Task B", 1.0),
        ],
    )
    resp = await get_planned_vs_actual(db, USER_ID, QUERY_DATE)

    by_id = {t.task_id: t for t in resp.tasks}
    assert by_id[TASK_A].planned_hours == pytest.approx(3.5)
    assert by_id[TASK_A].actual_hours == pytest.approx(2.0)
    assert by_id[TASK_B].planned_hours == pytest.approx(0.0)
    assert by_id[TASK_B].actual_hours == pytest.approx(1.0)
