from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.time_entry import TimeEntry
from app.schemas.time_entry import TimeEntryStart
from app.services.time_entry_service import (
    delete_time_entry,
    list_time_entries,
    start_timer,
    stop_timer,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TASK_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")
ENTRY_ID = uuid.UUID("00000000-0000-0000-0000-cccccccccccc")


def _make_fake_entry(**overrides: object) -> MagicMock:
    defaults: dict[str, object] = {
        "id": ENTRY_ID,
        "task_id": TASK_ID,
        "started_at": datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
        "ended_at": None,
        "duration_seconds": None,
        "created_at": datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    fake = MagicMock(spec=TimeEntry)
    for k, v in defaults.items():
        setattr(fake, k, v)
    return fake


# ---------------------------------------------------------------------------
# start_timer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_timer_returns_time_entry() -> None:
    """start_timer must add, commit, refresh and return TimeEntry."""
    db = AsyncMock()
    # Mock for task ownership check
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    # Mock for active timer check
    mock_active_result = MagicMock()
    mock_active_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [mock_task_result, mock_active_result]

    data = TimeEntryStart(task_id=TASK_ID)
    result = await start_timer(db=db, user_id=USER_ID, data=data)

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    assert isinstance(result, TimeEntry)


@pytest.mark.asyncio
async def test_start_timer_raises_404_for_wrong_task_owner() -> None:
    """start_timer must raise 404 if task doesn't belong to user."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    data = TimeEntryStart(task_id=TASK_ID)
    with pytest.raises(HTTPException) as exc_info:
        await start_timer(db=db, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_start_timer_raises_409_when_active_timer_exists() -> None:
    """start_timer must raise 409 when user already has an active timer."""
    db = AsyncMock()
    # Task ownership OK
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    # Active timer found
    mock_active_result = MagicMock()
    mock_active_result.scalar_one_or_none.return_value = _make_fake_entry()
    db.execute.side_effect = [mock_task_result, mock_active_result]

    data = TimeEntryStart(task_id=TASK_ID)
    with pytest.raises(HTTPException) as exc_info:
        await start_timer(db=db, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 409
    assert "active timer" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_start_timer_query_checks_user_for_active() -> None:
    """Active timer check must JOIN through Task/Project and filter user_id."""
    db = AsyncMock()
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    mock_active_result = MagicMock()
    mock_active_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [mock_task_result, mock_active_result]

    data = TimeEntryStart(task_id=TASK_ID)
    await start_timer(db=db, user_id=USER_ID, data=data)

    # The second execute call is the active timer check
    active_stmt = db.execute.call_args_list[1][0][0]
    compiled = str(active_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tasks" in compiled.lower()
    assert "projects" in compiled.lower()
    assert USER_ID.hex in compiled


@pytest.mark.asyncio
async def test_start_timer_uses_provided_started_at() -> None:
    """start_timer must use the provided started_at datetime."""
    db = AsyncMock()
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    mock_active_result = MagicMock()
    mock_active_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [mock_task_result, mock_active_result]

    custom_time = datetime(2026, 5, 1, 14, 30, tzinfo=UTC)
    data = TimeEntryStart(task_id=TASK_ID, started_at=custom_time)
    result = await start_timer(db=db, user_id=USER_ID, data=data)

    assert result.started_at == custom_time


@pytest.mark.asyncio
async def test_start_timer_detail_on_task_not_found() -> None:
    """start_timer must say 'Task not found'."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    data = TimeEntryStart(task_id=TASK_ID)
    with pytest.raises(HTTPException) as exc_info:
        await start_timer(db=db, user_id=USER_ID, data=data)

    assert exc_info.value.detail == "Task not found"


@pytest.mark.asyncio
async def test_start_timer_detail_on_active_timer() -> None:
    """start_timer must mention 'active timer' in 409 detail."""
    db = AsyncMock()
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    mock_active_result = MagicMock()
    mock_active_result.scalar_one_or_none.return_value = _make_fake_entry()
    db.execute.side_effect = [mock_task_result, mock_active_result]

    data = TimeEntryStart(task_id=TASK_ID)
    with pytest.raises(HTTPException) as exc_info:
        await start_timer(db=db, user_id=USER_ID, data=data)

    assert "active timer" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# stop_timer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_timer_sets_ended_at_and_duration() -> None:
    """stop_timer must set ended_at and compute duration_seconds."""
    started = datetime.now(UTC) - timedelta(hours=1)
    fake = _make_fake_entry(started_at=started, ended_at=None)
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    result = await stop_timer(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    assert result.ended_at is not None
    assert result.duration_seconds is not None
    assert result.duration_seconds > 0
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_timer_raises_404_when_not_found() -> None:
    """stop_timer must raise 404 when entry not found."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await stop_timer(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_stop_timer_raises_409_when_already_stopped() -> None:
    """stop_timer must raise 409 when timer already has ended_at."""
    fake = _make_fake_entry(
        ended_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        duration_seconds=3600,
    )
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await stop_timer(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 409
    assert "already stopped" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_stop_timer_query_joins_for_ownership() -> None:
    """stop_timer query must JOIN tasks and projects for ownership."""
    fake = _make_fake_entry()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    await stop_timer(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tasks" in compiled.lower()
    assert "projects" in compiled.lower()
    assert "JOIN" in compiled.upper()


@pytest.mark.asyncio
async def test_stop_timer_computes_duration_correctly() -> None:
    """stop_timer must compute duration as (ended_at - started_at) seconds."""
    started = datetime.now(UTC) - timedelta(seconds=120)
    fake = _make_fake_entry(started_at=started, ended_at=None)
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    result = await stop_timer(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    assert isinstance(result.duration_seconds, int)
    # Should be approximately 120 seconds (within 5s tolerance)
    assert 115 <= result.duration_seconds <= 125


# ---------------------------------------------------------------------------
# list_time_entries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_entries_returns_list() -> None:
    """list_time_entries must return a list of entries."""
    fake1 = _make_fake_entry()
    fake2 = _make_fake_entry()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake1, fake2]
    db.execute.return_value = mock_result

    result = await list_time_entries(db=db, user_id=USER_ID)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_entries_returns_empty() -> None:
    """list_time_entries must return empty list, not 404."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    result = await list_time_entries(db=db, user_id=USER_ID)

    assert result == []


@pytest.mark.asyncio
async def test_list_entries_filters_by_task_id() -> None:
    """list_time_entries query must filter by task_id when provided."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_time_entries(db=db, user_id=USER_ID, task_id=TASK_ID)

    compiled = str(
        db.execute.call_args[0][0].compile(compile_kwargs={"literal_binds": True})
    )
    assert TASK_ID.hex in compiled


@pytest.mark.asyncio
async def test_list_entries_filters_by_date() -> None:
    """list_time_entries query must filter by date range on started_at."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_time_entries(
        db=db, user_id=USER_ID, query_date=date(2026, 5, 1)
    )

    compiled = str(
        db.execute.call_args[0][0].compile(compile_kwargs={"literal_binds": True})
    )
    assert "2026-05-01" in compiled


@pytest.mark.asyncio
async def test_list_entries_scopes_to_user() -> None:
    """list_time_entries query must JOIN through Task/Project for user scope."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_time_entries(db=db, user_id=USER_ID)

    compiled = str(
        db.execute.call_args[0][0].compile(compile_kwargs={"literal_binds": True})
    )
    assert "projects" in compiled.lower()
    assert "JOIN" in compiled.upper()
    assert USER_ID.hex in compiled


# ---------------------------------------------------------------------------
# delete_time_entry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_entry_removes_and_commits() -> None:
    """delete_time_entry must delete and commit."""
    fake = _make_fake_entry()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    await delete_time_entry(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    db.delete.assert_awaited_once_with(fake)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_entry_raises_404_when_not_found() -> None:
    """delete_time_entry must raise 404 for missing/unauthorized entry."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_time_entry(db=db, entry_id=ENTRY_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Time entry not found"
