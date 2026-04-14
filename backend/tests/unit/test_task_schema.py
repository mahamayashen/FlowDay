from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

# ---------------------------------------------------------------------------
# TaskCreate
# ---------------------------------------------------------------------------


def test_create_requires_title() -> None:
    """TaskCreate must require title."""
    t = TaskCreate(title="Write tests")
    assert t.title == "Write tests"


def test_create_optional_fields_default_correctly() -> None:
    """Optional fields default to None; priority to 'medium', status to 'todo'."""
    t = TaskCreate(title="Work")
    assert t.description is None
    assert t.estimate_minutes is None
    assert t.due_date is None
    assert t.priority == "medium"
    assert t.status == "todo"


def test_create_with_all_fields() -> None:
    """TaskCreate must accept all optional fields."""
    t = TaskCreate(
        title="Write tests",
        description="Unit tests for task service",
        estimate_minutes=60,
        priority="high",
        status="in_progress",
        due_date=date(2026, 5, 1),
    )
    assert t.description == "Unit tests for task service"
    assert t.estimate_minutes == 60
    assert t.priority == "high"
    assert t.status == "in_progress"
    assert t.due_date == date(2026, 5, 1)


def test_create_rejects_empty_title() -> None:
    """TaskCreate must reject empty string title."""
    with pytest.raises(ValidationError):
        TaskCreate(title="")


def test_create_rejects_blank_title() -> None:
    """TaskCreate must reject whitespace-only title."""
    with pytest.raises(ValidationError):
        TaskCreate(title="   ")


def test_create_rejects_title_too_long() -> None:
    """TaskCreate must reject title longer than 255 characters."""
    with pytest.raises(ValidationError):
        TaskCreate(title="A" * 256)


def test_create_strips_title_whitespace() -> None:
    """TaskCreate must strip leading/trailing whitespace from title."""
    t = TaskCreate(title="  Write tests  ")
    assert t.title == "Write tests"


def test_create_rejects_negative_estimate_minutes() -> None:
    """TaskCreate must reject negative estimate_minutes."""
    with pytest.raises(ValidationError):
        TaskCreate(title="Work", estimate_minutes=-1)


def test_create_accepts_zero_estimate_minutes() -> None:
    """TaskCreate must accept zero estimate_minutes."""
    t = TaskCreate(title="Work", estimate_minutes=0)
    assert t.estimate_minutes == 0


def test_create_rejects_invalid_priority() -> None:
    """TaskCreate must reject invalid priority values."""
    with pytest.raises(ValidationError):
        TaskCreate(title="Work", priority="critical")


def test_create_rejects_invalid_status() -> None:
    """TaskCreate must reject invalid status values."""
    with pytest.raises(ValidationError):
        TaskCreate(title="Work", status="skipped")


def test_create_accepts_valid_priorities() -> None:
    """TaskCreate must accept all valid priority values."""
    for p in ("low", "medium", "high", "urgent"):
        t = TaskCreate(title="Work", priority=p)
        assert t.priority == p


def test_create_accepts_valid_statuses() -> None:
    """TaskCreate must accept all valid status values."""
    for s in ("todo", "in_progress", "done"):
        t = TaskCreate(title="Work", status=s)
        assert t.status == s


def test_create_rejects_missing_title() -> None:
    """TaskCreate without title must raise ValidationError."""
    with pytest.raises(ValidationError):
        TaskCreate()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TaskUpdate
# ---------------------------------------------------------------------------


def test_update_all_fields_optional() -> None:
    """TaskUpdate must allow empty (no fields set)."""
    t = TaskUpdate()
    assert t.title is None
    assert t.description is None
    assert t.estimate_minutes is None
    assert t.priority is None
    assert t.status is None
    assert t.due_date is None


def test_update_partial_fields() -> None:
    """TaskUpdate must accept partial updates."""
    t = TaskUpdate(title="New Title")
    assert t.title == "New Title"
    assert t.description is None


def test_update_rejects_empty_title() -> None:
    """TaskUpdate must reject empty string title."""
    with pytest.raises(ValidationError):
        TaskUpdate(title="")


def test_update_rejects_blank_title() -> None:
    """TaskUpdate must reject whitespace-only title."""
    with pytest.raises(ValidationError):
        TaskUpdate(title="   ")


def test_update_rejects_title_too_long() -> None:
    """TaskUpdate must reject title longer than 255 characters."""
    with pytest.raises(ValidationError):
        TaskUpdate(title="A" * 256)


def test_update_rejects_negative_estimate_minutes() -> None:
    """TaskUpdate must reject negative estimate_minutes."""
    with pytest.raises(ValidationError):
        TaskUpdate(estimate_minutes=-1)


def test_update_rejects_invalid_priority() -> None:
    """TaskUpdate must reject invalid priority values."""
    with pytest.raises(ValidationError):
        TaskUpdate(priority="critical")


def test_update_rejects_invalid_status() -> None:
    """TaskUpdate must reject invalid status values."""
    with pytest.raises(ValidationError):
        TaskUpdate(status="skipped")


def test_update_rejects_empty_string_priority() -> None:
    """TaskUpdate must reject empty string as priority."""
    with pytest.raises(ValidationError):
        TaskUpdate(priority="")


def test_update_rejects_empty_string_status() -> None:
    """TaskUpdate must reject empty string as status."""
    with pytest.raises(ValidationError):
        TaskUpdate(status="")


# ---------------------------------------------------------------------------
# TaskResponse
# ---------------------------------------------------------------------------


def test_response_from_attributes() -> None:
    """TaskResponse must support from_attributes (ORM mode)."""
    assert TaskResponse.model_config.get("from_attributes") is True


def test_response_round_trip() -> None:
    """TaskResponse must serialize all task fields."""
    now = datetime.now(UTC)
    tid = uuid.uuid4()
    pid = uuid.uuid4()
    resp = TaskResponse(
        id=tid,
        project_id=pid,
        title="Test Task",
        description="A description",
        estimate_minutes=30,
        priority="high",
        status="done",
        due_date=date(2026, 5, 1),
        created_at=now,
        completed_at=now,
    )
    assert resp.id == tid
    assert resp.project_id == pid
    assert resp.title == "Test Task"
    assert resp.description == "A description"
    assert resp.estimate_minutes == 30
    assert resp.priority == "high"
    assert resp.status == "done"
    assert resp.due_date == date(2026, 5, 1)
    assert resp.completed_at == now
