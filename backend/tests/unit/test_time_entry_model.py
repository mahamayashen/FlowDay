from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.models.time_entry import TimeEntry


def test_time_entry_table_name() -> None:
    """TimeEntry.__tablename__ must be 'time_entries'."""
    assert TimeEntry.__tablename__ == "time_entries"


def test_time_entry_has_required_columns() -> None:
    """TimeEntry must have all columns from DATA_MODEL.md."""
    columns = {c.name for c in inspect(TimeEntry).columns}
    expected = {
        "id",
        "task_id",
        "started_at",
        "ended_at",
        "duration_seconds",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_time_entry_id_is_uuid() -> None:
    """TimeEntry.id column type must be UUID."""
    col = inspect(TimeEntry).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_time_entry_task_id_is_foreign_key() -> None:
    """TimeEntry.task_id must reference tasks.id."""
    col = inspect(TimeEntry).columns["task_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "tasks.id" in fk_targets


def test_time_entry_task_id_cascade_delete() -> None:
    """TimeEntry.task_id FK must have ondelete CASCADE."""
    col = inspect(TimeEntry).columns["task_id"]
    for fk in col.foreign_keys:
        if fk.target_fullname == "tasks.id":
            assert fk.ondelete == "CASCADE"


def test_time_entry_task_id_not_nullable() -> None:
    """TimeEntry.task_id must be NOT NULL."""
    col = inspect(TimeEntry).columns["task_id"]
    assert col.nullable is False


def test_time_entry_started_at_not_nullable() -> None:
    """TimeEntry.started_at must be NOT NULL."""
    col = inspect(TimeEntry).columns["started_at"]
    assert col.nullable is False


def test_time_entry_started_at_is_datetime_tz() -> None:
    """TimeEntry.started_at must be DateTime with timezone."""
    col = inspect(TimeEntry).columns["started_at"]
    assert col.type.timezone is True


def test_time_entry_ended_at_is_nullable() -> None:
    """TimeEntry.ended_at must be nullable (active timer has no end)."""
    col = inspect(TimeEntry).columns["ended_at"]
    assert col.nullable is True


def test_time_entry_ended_at_is_datetime_tz() -> None:
    """TimeEntry.ended_at must be DateTime with timezone."""
    col = inspect(TimeEntry).columns["ended_at"]
    assert col.type.timezone is True


def test_time_entry_duration_seconds_is_nullable() -> None:
    """TimeEntry.duration_seconds must be nullable (computed on stop)."""
    col = inspect(TimeEntry).columns["duration_seconds"]
    assert col.nullable is True


def test_time_entry_duration_seconds_is_integer() -> None:
    """TimeEntry.duration_seconds column type must be INTEGER."""
    col = inspect(TimeEntry).columns["duration_seconds"]
    assert "INTEGER" in str(col.type).upper()


def test_time_entry_has_task_started_index() -> None:
    """TimeEntry must have an index on (task_id, started_at)."""
    indexes = {idx.name for idx in inspect(TimeEntry).mapped_table.indexes}
    assert "idx_time_entry_task_started" in indexes


def test_time_entry_repr_contains_id() -> None:
    """TimeEntry.__repr__ should include the entry id."""
    entry_id = uuid.uuid4()
    entry = TimeEntry(id=entry_id, task_id=uuid.uuid4())
    assert str(entry_id) in repr(entry)
