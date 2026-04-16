from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.models.schedule_block import ScheduleBlock, ScheduleBlockSource


def test_schedule_block_table_name() -> None:
    """ScheduleBlock.__tablename__ must be 'schedule_blocks'."""
    assert ScheduleBlock.__tablename__ == "schedule_blocks"


def test_schedule_block_has_required_columns() -> None:
    """ScheduleBlock must have all columns from DATA_MODEL.md."""
    columns = {c.name for c in inspect(ScheduleBlock).columns}
    expected = {
        "id",
        "task_id",
        "date",
        "start_hour",
        "end_hour",
        "source",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_schedule_block_id_is_uuid() -> None:
    """ScheduleBlock.id column type must be UUID."""
    col = inspect(ScheduleBlock).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_schedule_block_task_id_is_foreign_key() -> None:
    """ScheduleBlock.task_id must reference tasks.id."""
    col = inspect(ScheduleBlock).columns["task_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "tasks.id" in fk_targets


def test_schedule_block_task_id_cascade_delete() -> None:
    """ScheduleBlock.task_id FK must have ondelete CASCADE."""
    col = inspect(ScheduleBlock).columns["task_id"]
    for fk in col.foreign_keys:
        if fk.target_fullname == "tasks.id":
            assert fk.ondelete == "CASCADE"


def test_schedule_block_task_id_not_nullable() -> None:
    """ScheduleBlock.task_id must be NOT NULL."""
    col = inspect(ScheduleBlock).columns["task_id"]
    assert col.nullable is False


def test_schedule_block_date_not_nullable() -> None:
    """ScheduleBlock.date must be NOT NULL."""
    col = inspect(ScheduleBlock).columns["date"]
    assert col.nullable is False


def test_schedule_block_start_hour_not_nullable() -> None:
    """ScheduleBlock.start_hour must be NOT NULL."""
    col = inspect(ScheduleBlock).columns["start_hour"]
    assert col.nullable is False


def test_schedule_block_start_hour_is_numeric() -> None:
    """ScheduleBlock.start_hour column type must be Numeric."""
    col = inspect(ScheduleBlock).columns["start_hour"]
    assert "NUMERIC" in str(col.type).upper()


def test_schedule_block_end_hour_not_nullable() -> None:
    """ScheduleBlock.end_hour must be NOT NULL."""
    col = inspect(ScheduleBlock).columns["end_hour"]
    assert col.nullable is False


def test_schedule_block_end_hour_is_numeric() -> None:
    """ScheduleBlock.end_hour column type must be Numeric."""
    col = inspect(ScheduleBlock).columns["end_hour"]
    assert "NUMERIC" in str(col.type).upper()


def test_schedule_block_source_has_default() -> None:
    """ScheduleBlock.source column must default to MANUAL."""
    col = inspect(ScheduleBlock).columns["source"]
    assert col.default is not None
    assert col.default.arg == ScheduleBlockSource.MANUAL  # type: ignore[attr-defined]


def test_schedule_block_source_enum_values() -> None:
    """ScheduleBlockSource enum must have manual and google_calendar values."""
    assert ScheduleBlockSource.MANUAL.value == "manual"
    assert ScheduleBlockSource.GOOGLE_CALENDAR.value == "google_calendar"


def test_schedule_block_has_source_check_constraint() -> None:
    """ScheduleBlock must have a CHECK constraint on source."""
    constraints = {c.name for c in ScheduleBlock.__table__.constraints}  # type: ignore[attr-defined]
    assert "ck_schedule_blocks_source" in constraints


def test_schedule_block_has_end_gt_start_check_constraint() -> None:
    """ScheduleBlock must have a CHECK constraint end_hour > start_hour."""
    constraints = {c.name for c in ScheduleBlock.__table__.constraints}  # type: ignore[attr-defined]
    assert "ck_schedule_blocks_end_gt_start" in constraints


def test_schedule_block_has_date_task_index() -> None:
    """ScheduleBlock must have an index on (date, task_id)."""
    indexes = {idx.name for idx in inspect(ScheduleBlock).mapped_table.indexes}
    assert "idx_schedule_block_date" in indexes


def test_schedule_block_repr_contains_id() -> None:
    """ScheduleBlock.__repr__ should include the block id."""
    block_id = uuid.uuid4()
    block = ScheduleBlock(id=block_id, task_id=uuid.uuid4())
    assert str(block_id) in repr(block)
