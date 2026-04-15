from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.models.task import Task, TaskPriority, TaskStatus


def test_task_table_name_is_tasks() -> None:
    """Task.__tablename__ must be 'tasks'."""
    assert Task.__tablename__ == "tasks"


def test_task_model_has_required_columns() -> None:
    """Task model must have all columns defined in DATA_MODEL.md."""
    columns = {c.name for c in inspect(Task).columns}
    expected = {
        "id",
        "project_id",
        "title",
        "description",
        "estimate_minutes",
        "priority",
        "status",
        "due_date",
        "created_at",
        "completed_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_task_id_is_uuid() -> None:
    """Task.id column type must be UUID."""
    col = inspect(Task).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_task_project_id_is_foreign_key() -> None:
    """Task.project_id must reference projects.id."""
    col = inspect(Task).columns["project_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "projects.id" in fk_targets


def test_task_project_id_not_nullable() -> None:
    """Task.project_id must be NOT NULL."""
    col = inspect(Task).columns["project_id"]
    assert col.nullable is False


def test_task_title_not_nullable() -> None:
    """Task.title must be NOT NULL."""
    col = inspect(Task).columns["title"]
    assert col.nullable is False


def test_task_description_nullable() -> None:
    """Task.description must be NULLABLE."""
    col = inspect(Task).columns["description"]
    assert col.nullable is True


def test_task_estimate_minutes_nullable() -> None:
    """Task.estimate_minutes must be NULLABLE."""
    col = inspect(Task).columns["estimate_minutes"]
    assert col.nullable is True


def test_task_due_date_nullable() -> None:
    """Task.due_date must be NULLABLE."""
    col = inspect(Task).columns["due_date"]
    assert col.nullable is True


def test_task_completed_at_nullable() -> None:
    """Task.completed_at must be NULLABLE."""
    col = inspect(Task).columns["completed_at"]
    assert col.nullable is True


def test_task_priority_has_default() -> None:
    """Task.priority column must have a default of TaskPriority.MEDIUM."""
    col = inspect(Task).columns["priority"]
    assert col.default is not None
    assert col.default.arg == TaskPriority.MEDIUM


def test_task_priority_enum_values() -> None:
    """TaskPriority enum must have low, medium, high, urgent values."""
    assert TaskPriority.LOW.value == "low"
    assert TaskPriority.MEDIUM.value == "medium"
    assert TaskPriority.HIGH.value == "high"
    assert TaskPriority.URGENT.value == "urgent"


def test_task_status_has_default() -> None:
    """Task.status column must have a default of TaskStatus.TODO."""
    col = inspect(Task).columns["status"]
    assert col.default is not None
    assert col.default.arg == TaskStatus.TODO


def test_task_status_enum_values() -> None:
    """TaskStatus enum must have todo, in_progress, done values."""
    assert TaskStatus.TODO.value == "todo"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.DONE.value == "done"


def test_task_has_priority_check_constraint() -> None:
    """Task must have a CHECK constraint on priority column."""
    constraints = {c.name for c in Task.__table__.constraints}
    assert "ck_tasks_priority" in constraints


def test_task_has_status_check_constraint() -> None:
    """Task must have a CHECK constraint on status column."""
    constraints = {c.name for c in Task.__table__.constraints}
    assert "ck_tasks_status" in constraints


def test_task_has_project_status_index() -> None:
    """Task must have a composite index on (project_id, status)."""
    index_names = {idx.name for idx in Task.__table__.indexes}
    assert "idx_task_project_status" in index_names


def test_task_repr_contains_title() -> None:
    """Task.__repr__ should include the task title for debugging."""
    t = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="My Task",
    )
    assert "My Task" in repr(t)
