from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.time_entry import TimeEntryResponse, TimeEntryStart

TASK_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")

# ---------------------------------------------------------------------------
# TimeEntryStart
# ---------------------------------------------------------------------------


def test_start_with_task_id_only() -> None:
    """TimeEntryStart must accept task_id alone; started_at defaults to None."""
    s = TimeEntryStart(task_id=TASK_ID)
    assert s.task_id == TASK_ID
    assert s.started_at is None


def test_start_with_explicit_started_at() -> None:
    """TimeEntryStart must accept an explicit started_at datetime."""
    now = datetime.now(UTC)
    s = TimeEntryStart(task_id=TASK_ID, started_at=now)
    assert s.started_at == now


def test_start_rejects_missing_task_id() -> None:
    """TimeEntryStart without task_id must raise ValidationError."""
    with pytest.raises(ValidationError):
        TimeEntryStart()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TimeEntryResponse
# ---------------------------------------------------------------------------


def test_response_from_attributes() -> None:
    """TimeEntryResponse must support from_attributes (ORM mode)."""
    assert TimeEntryResponse.model_config.get("from_attributes") is True


def test_response_round_trip() -> None:
    """TimeEntryResponse must serialize all fields."""
    now = datetime.now(UTC)
    entry_id = uuid.uuid4()
    resp = TimeEntryResponse(
        id=entry_id,
        task_id=TASK_ID,
        started_at=now,
        ended_at=now,
        duration_seconds=3600,
        created_at=now,
    )
    assert resp.id == entry_id
    assert resp.task_id == TASK_ID
    assert resp.duration_seconds == 3600


def test_response_allows_null_ended_at() -> None:
    """TimeEntryResponse must allow ended_at=None (active timer)."""
    now = datetime.now(UTC)
    resp = TimeEntryResponse(
        id=uuid.uuid4(),
        task_id=TASK_ID,
        started_at=now,
        ended_at=None,
        duration_seconds=None,
        created_at=now,
    )
    assert resp.ended_at is None


def test_response_allows_null_duration() -> None:
    """TimeEntryResponse must allow duration_seconds=None (active timer)."""
    now = datetime.now(UTC)
    resp = TimeEntryResponse(
        id=uuid.uuid4(),
        task_id=TASK_ID,
        started_at=now,
        ended_at=None,
        duration_seconds=None,
        created_at=now,
    )
    assert resp.duration_seconds is None
