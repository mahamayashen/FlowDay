from __future__ import annotations

import uuid
from datetime import date, datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.schedule_block import ScheduleBlock, ScheduleBlockSource
from app.schemas.schedule_block import ScheduleBlockCreate, ScheduleBlockUpdate
from app.services.schedule_block_service import (
    create_schedule_block,
    delete_schedule_block,
    get_schedule_block,
    list_schedule_blocks,
    update_schedule_block,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")
TASK_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")
BLOCK_ID = uuid.UUID("00000000-0000-0000-0000-cccccccccccc")


def _make_fake_block(**overrides: object) -> MagicMock:
    defaults = {
        "id": BLOCK_ID,
        "task_id": TASK_ID,
        "date": date(2026, 5, 1),
        "start_hour": Decimal("9.00"),
        "end_hour": Decimal("10.00"),
        "source": ScheduleBlockSource.MANUAL,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    fake = MagicMock(spec=ScheduleBlock)
    for k, v in defaults.items():
        setattr(fake, k, v)
    return fake


# ---------------------------------------------------------------------------
# _get_block_with_ownership
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_block_returns_block_for_owner() -> None:
    """get_schedule_block must return block when user owns it."""
    fake = _make_fake_block()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    result = await get_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID)

    assert result == fake


@pytest.mark.asyncio
async def test_get_block_raises_404_when_not_found() -> None:
    """get_schedule_block must raise 404 when block doesn't exist or user doesn't own it."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Schedule block not found"


@pytest.mark.asyncio
async def test_get_block_query_joins_task_and_project() -> None:
    """get_schedule_block query must JOIN tasks and projects for ownership."""
    fake = _make_fake_block()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    await get_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tasks" in compiled.lower()
    assert "projects" in compiled.lower()
    assert "JOIN" in compiled.upper()


# ---------------------------------------------------------------------------
# create_schedule_block
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_block_returns_block() -> None:
    """create_schedule_block must add, commit, refresh and return block."""
    db = AsyncMock()
    # Mock for task ownership check
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    # Mock for overlap check
    mock_overlap_result = MagicMock()
    mock_overlap_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [mock_task_result, mock_overlap_result]

    data = ScheduleBlockCreate(
        task_id=TASK_ID,
        date=date(2026, 5, 1),
        start_hour=Decimal("9"),
        end_hour=Decimal("10"),
    )
    result = await create_schedule_block(db=db, user_id=USER_ID, data=data)

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    assert isinstance(result, ScheduleBlock)


@pytest.mark.asyncio
async def test_create_block_raises_404_for_wrong_task_owner() -> None:
    """create_schedule_block must raise 404 if task doesn't belong to user."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    data = ScheduleBlockCreate(
        task_id=TASK_ID,
        date=date(2026, 5, 1),
        start_hour=Decimal("9"),
        end_hour=Decimal("10"),
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_schedule_block(db=db, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_block_raises_409_on_overlap() -> None:
    """create_schedule_block must raise 409 when overlapping block exists."""
    db = AsyncMock()
    # Task ownership OK
    mock_task_result = MagicMock()
    mock_task_result.scalar_one_or_none.return_value = MagicMock()
    # Overlap found
    mock_overlap_result = MagicMock()
    mock_overlap_result.scalar_one_or_none.return_value = _make_fake_block()
    db.execute.side_effect = [mock_task_result, mock_overlap_result]

    data = ScheduleBlockCreate(
        task_id=TASK_ID,
        date=date(2026, 5, 1),
        start_hour=Decimal("9"),
        end_hour=Decimal("10"),
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_schedule_block(db=db, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 409
    assert "overlap" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# list_schedule_blocks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_blocks_returns_blocks_for_date() -> None:
    """list_schedule_blocks must return blocks for the given date."""
    fake1 = _make_fake_block()
    fake2 = _make_fake_block()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake1, fake2]
    db.execute.return_value = mock_result

    result = await list_schedule_blocks(db=db, user_id=USER_ID, query_date=date(2026, 5, 1))

    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_blocks_returns_empty_for_no_blocks() -> None:
    """list_schedule_blocks must return empty list, not 404."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    result = await list_schedule_blocks(db=db, user_id=USER_ID, query_date=date(2026, 5, 1))

    assert result == []


@pytest.mark.asyncio
async def test_list_blocks_scopes_to_user() -> None:
    """list_schedule_blocks query must filter by user ownership."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_schedule_blocks(db=db, user_id=USER_ID, query_date=date(2026, 5, 1))

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "projects" in compiled.lower()
    assert "JOIN" in compiled.upper()


# ---------------------------------------------------------------------------
# update_schedule_block
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_block_applies_changes() -> None:
    """update_schedule_block must apply provided fields."""
    fake = _make_fake_block()
    db = AsyncMock()
    # Ownership query
    mock_own_result = MagicMock()
    mock_own_result.scalar_one_or_none.return_value = fake
    # Overlap check
    mock_overlap_result = MagicMock()
    mock_overlap_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [mock_own_result, mock_overlap_result]

    data = ScheduleBlockUpdate(start_hour=Decimal("8"), end_hour=Decimal("11"))
    result = await update_schedule_block(
        db=db, block_id=BLOCK_ID, user_id=USER_ID, data=data,
    )

    assert result == fake
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_block_raises_404_when_not_found() -> None:
    """update_schedule_block must raise 404 for missing/unauthorized block."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    data = ScheduleBlockUpdate(start_hour=Decimal("8"))
    with pytest.raises(HTTPException) as exc_info:
        await update_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_block_raises_409_on_overlap() -> None:
    """update_schedule_block must raise 409 when update causes overlap."""
    fake = _make_fake_block()
    db = AsyncMock()
    mock_own_result = MagicMock()
    mock_own_result.scalar_one_or_none.return_value = fake
    # Overlap found (different block)
    other_block = _make_fake_block(id=uuid.uuid4())
    mock_overlap_result = MagicMock()
    mock_overlap_result.scalar_one_or_none.return_value = other_block
    db.execute.side_effect = [mock_own_result, mock_overlap_result]

    data = ScheduleBlockUpdate(start_hour=Decimal("9"), end_hour=Decimal("10"))
    with pytest.raises(HTTPException) as exc_info:
        await update_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# delete_schedule_block
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_block_removes_block() -> None:
    """delete_schedule_block must delete and commit."""
    fake = _make_fake_block()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    await delete_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID)

    db.delete.assert_awaited_once_with(fake)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_block_raises_404_when_not_found() -> None:
    """delete_schedule_block must raise 404 for missing/unauthorized block."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_schedule_block(db=db, block_id=BLOCK_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
