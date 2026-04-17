from __future__ import annotations

import uuid
from collections import namedtuple
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.analytics_service import (
    align_to_monday,
    compute_accuracy_pct,
    get_weekly_stats,
)

# ---------------------------------------------------------------------------
# Cycle 1 — align_to_monday
# ---------------------------------------------------------------------------


def test_align_to_monday_already_monday() -> None:
    assert align_to_monday(date(2026, 4, 13)) == date(2026, 4, 13)


def test_align_to_monday_from_wednesday() -> None:
    assert align_to_monday(date(2026, 4, 15)) == date(2026, 4, 13)


def test_align_to_monday_from_sunday() -> None:
    assert align_to_monday(date(2026, 4, 19)) == date(2026, 4, 13)


# ---------------------------------------------------------------------------
# Cycle 2 — compute_accuracy_pct
# ---------------------------------------------------------------------------


def test_accuracy_pct_normal_case() -> None:
    assert compute_accuracy_pct(2.0, 1.5) == 75.0


def test_accuracy_pct_zero_planned() -> None:
    assert compute_accuracy_pct(0.0, 1.5) == 0.0


def test_accuracy_pct_over_100_percent() -> None:
    assert compute_accuracy_pct(2.0, 4.0) == 200.0


def test_accuracy_pct_exact_match() -> None:
    assert compute_accuracy_pct(3.0, 3.0) == 100.0


# ---------------------------------------------------------------------------
# Cycle 3 — get_weekly_stats (mocked DB)
# ---------------------------------------------------------------------------

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PROJ_X = uuid.UUID("00000000-0000-0000-0000-000000001001")
PROJ_Y = uuid.UUID("00000000-0000-0000-0000-000000001002")

PlannedProjectRow = namedtuple(
    "PlannedProjectRow", ["id", "name", "color", "planned_hours"]
)
ActualProjectRow = namedtuple(
    "ActualProjectRow", ["id", "name", "color", "actual_hours"]
)

WEEK_MONDAY = date(2026, 4, 13)  # known Monday


def _mock_weekly_db(
    planned_rows: list[PlannedProjectRow],
    actual_rows: list[ActualProjectRow],
) -> AsyncMock:
    db = AsyncMock()
    planned_result = MagicMock()
    planned_result.all.return_value = planned_rows
    actual_result = MagicMock()
    actual_result.all.return_value = actual_rows
    db.execute.side_effect = [planned_result, actual_result]
    return db


@pytest.mark.asyncio
async def test_get_weekly_stats_mixed_projects() -> None:
    """Two projects: one with planned+actual, one with only planned."""
    db = _mock_weekly_db(
        planned_rows=[
            PlannedProjectRow(PROJ_X, "Project X", "#ff0000", 4.0),
            PlannedProjectRow(PROJ_Y, "Project Y", "#00ff00", 2.0),
        ],
        actual_rows=[
            ActualProjectRow(PROJ_X, "Project X", "#ff0000", 3.0),
        ],
    )
    resp = await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    assert resp.week_start == WEEK_MONDAY
    assert resp.week_end == date(2026, 4, 19)

    by_id = {p.project_id: p for p in resp.projects}
    assert by_id[PROJ_X].planned_hours == pytest.approx(4.0)
    assert by_id[PROJ_X].actual_hours == pytest.approx(3.0)
    assert by_id[PROJ_X].accuracy_pct == pytest.approx(75.0)

    assert by_id[PROJ_Y].planned_hours == pytest.approx(2.0)
    assert by_id[PROJ_Y].actual_hours == pytest.approx(0.0)
    assert by_id[PROJ_Y].accuracy_pct == pytest.approx(0.0)

    assert resp.summary.total_planned_hours == pytest.approx(6.0)
    assert resp.summary.total_actual_hours == pytest.approx(3.0)
    # Both projects have planned > 0: mean of [75.0, 0.0] = 37.5
    assert resp.summary.average_accuracy_pct == pytest.approx(37.5)


@pytest.mark.asyncio
async def test_get_weekly_stats_empty_week() -> None:
    """No data at all → empty projects list, zero summary."""
    db = _mock_weekly_db([], [])
    resp = await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    assert resp.projects == []
    assert resp.summary.total_planned_hours == 0.0
    assert resp.summary.total_actual_hours == 0.0
    assert resp.summary.average_accuracy_pct == 0.0


@pytest.mark.asyncio
async def test_get_weekly_stats_only_actual() -> None:
    """Unplanned work: actual but no schedule blocks."""
    db = _mock_weekly_db(
        planned_rows=[],
        actual_rows=[ActualProjectRow(PROJ_X, "Project X", "#ff0000", 2.0)],
    )
    resp = await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    assert len(resp.projects) == 1
    proj = resp.projects[0]
    assert proj.planned_hours == pytest.approx(0.0)
    assert proj.actual_hours == pytest.approx(2.0)
    assert proj.accuracy_pct == pytest.approx(0.0)
    # No projects with planned > 0 → average is 0.0
    assert resp.summary.average_accuracy_pct == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_get_weekly_stats_only_planned() -> None:
    """Planned but no actuals → accuracy 0%."""
    db = _mock_weekly_db(
        planned_rows=[PlannedProjectRow(PROJ_X, "Project X", "#ff0000", 3.0)],
        actual_rows=[],
    )
    resp = await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    assert len(resp.projects) == 1
    proj = resp.projects[0]
    assert proj.planned_hours == pytest.approx(3.0)
    assert proj.actual_hours == pytest.approx(0.0)
    assert proj.accuracy_pct == pytest.approx(0.0)
    assert resp.summary.average_accuracy_pct == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_get_weekly_stats_auto_aligns_to_monday() -> None:
    """Passing a Wednesday still returns a response with week_start on Monday."""
    db = _mock_weekly_db([], [])
    wednesday = date(2026, 4, 15)
    resp = await get_weekly_stats(db, USER_ID, wednesday)

    assert resp.week_start == WEEK_MONDAY  # aligned to Monday


# ---------------------------------------------------------------------------
# Cycle 4 — SQL query inspection
# ---------------------------------------------------------------------------


def _compile(stmt: object) -> str:
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_weekly_planned_query_joins_and_filters() -> None:
    """Planned query must JOIN ScheduleBlock→Task→Project, group by project."""
    db = _mock_weekly_db([], [])
    await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    planned_stmt = db.execute.call_args_list[0][0][0]
    compiled = _compile(planned_stmt)

    assert "schedule_blocks.task_id = tasks.id" in compiled.lower()
    assert "tasks.project_id = projects.id" in compiled.lower()
    assert "2026-04-13" in compiled  # week_start
    assert "2026-04-20" in compiled  # next_monday
    assert USER_ID.hex in compiled
    assert " - " in compiled  # end_hour - start_hour


@pytest.mark.asyncio
async def test_weekly_actual_query_joins_and_filters() -> None:
    """Actual query must JOIN TimeEntry→Task→Project, filter by datetime range."""
    db = _mock_weekly_db([], [])
    await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    actual_stmt = db.execute.call_args_list[1][0][0]
    compiled = _compile(actual_stmt)

    assert "time_entries.task_id = tasks.id" in compiled.lower()
    assert "tasks.project_id = projects.id" in compiled.lower()
    assert "2026-04-13" in compiled  # week_start_dt date part
    assert "2026-04-20" in compiled  # week_end_dt date part
    assert USER_ID.hex in compiled
    assert "3600" in compiled
    assert ">=" in compiled
    assert "< '2026-04-20" in compiled


@pytest.mark.asyncio
async def test_weekly_date_range_spans_seven_days() -> None:
    """Both queries must reference exactly the Monday and the following Monday."""
    db = _mock_weekly_db([], [])
    await get_weekly_stats(db, USER_ID, WEEK_MONDAY)

    planned_stmt = db.execute.call_args_list[0][0][0]
    actual_stmt = db.execute.call_args_list[1][0][0]

    planned_compiled = _compile(planned_stmt)
    actual_compiled = _compile(actual_stmt)

    # Monday 2026-04-13 and next Monday 2026-04-20 must both appear
    assert "2026-04-13" in planned_compiled
    assert "2026-04-20" in planned_compiled
    assert "2026-04-13" in actual_compiled
    assert "2026-04-20" in actual_compiled
