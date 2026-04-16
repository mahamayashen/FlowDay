from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.schedule_block import (
    ScheduleBlockCreate,
    ScheduleBlockResponse,
    ScheduleBlockUpdate,
)

TASK_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")

# ---------------------------------------------------------------------------
# ScheduleBlockCreate
# ---------------------------------------------------------------------------


def test_create_with_required_fields() -> None:
    """ScheduleBlockCreate must accept all required fields."""
    b = ScheduleBlockCreate(
        task_id=TASK_ID,
        date=date(2026, 5, 1),
        start_hour=Decimal("9.00"),
        end_hour=Decimal("10.50"),
    )
    assert b.task_id == TASK_ID
    assert b.date == date(2026, 5, 1)
    assert b.start_hour == Decimal("9.00")
    assert b.end_hour == Decimal("10.50")


def test_create_defaults_source_to_manual() -> None:
    """ScheduleBlockCreate.source must default to 'manual'."""
    b = ScheduleBlockCreate(
        task_id=TASK_ID, date=date(2026, 5, 1), start_hour=Decimal("9"), end_hour=Decimal("10"),
    )
    assert b.source == "manual"


def test_create_rejects_missing_task_id() -> None:
    """ScheduleBlockCreate without task_id must raise ValidationError."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(date=date(2026, 5, 1), start_hour=Decimal("9"), end_hour=Decimal("10"))  # type: ignore[call-arg]


def test_create_rejects_missing_date() -> None:
    """ScheduleBlockCreate without date must raise ValidationError."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(task_id=TASK_ID, start_hour=Decimal("9"), end_hour=Decimal("10"))  # type: ignore[call-arg]


def test_create_rejects_missing_start_hour() -> None:
    """ScheduleBlockCreate without start_hour must raise ValidationError."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(task_id=TASK_ID, date=date(2026, 5, 1), end_hour=Decimal("10"))  # type: ignore[call-arg]


def test_create_rejects_missing_end_hour() -> None:
    """ScheduleBlockCreate without end_hour must raise ValidationError."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(task_id=TASK_ID, date=date(2026, 5, 1), start_hour=Decimal("9"))  # type: ignore[call-arg]


def test_create_rejects_start_equal_end() -> None:
    """ScheduleBlockCreate must reject start_hour == end_hour."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            task_id=TASK_ID, date=date(2026, 5, 1),
            start_hour=Decimal("10"), end_hour=Decimal("10"),
        )


def test_create_rejects_start_gt_end() -> None:
    """ScheduleBlockCreate must reject start_hour > end_hour."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            task_id=TASK_ID, date=date(2026, 5, 1),
            start_hour=Decimal("15"), end_hour=Decimal("10"),
        )


def test_create_rejects_negative_start_hour() -> None:
    """ScheduleBlockCreate must reject negative start_hour."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            task_id=TASK_ID, date=date(2026, 5, 1),
            start_hour=Decimal("-1"), end_hour=Decimal("10"),
        )


def test_create_rejects_start_hour_above_24() -> None:
    """ScheduleBlockCreate must reject start_hour > 24."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            task_id=TASK_ID, date=date(2026, 5, 1),
            start_hour=Decimal("24.01"), end_hour=Decimal("25"),
        )


def test_create_rejects_end_hour_above_24() -> None:
    """ScheduleBlockCreate must reject end_hour > 24."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            task_id=TASK_ID, date=date(2026, 5, 1),
            start_hour=Decimal("9"), end_hour=Decimal("24.01"),
        )


def test_create_accepts_boundary_hours() -> None:
    """ScheduleBlockCreate must accept start_hour=0, end_hour=24."""
    b = ScheduleBlockCreate(
        task_id=TASK_ID, date=date(2026, 5, 1),
        start_hour=Decimal("0"), end_hour=Decimal("24"),
    )
    assert b.start_hour == Decimal("0")
    assert b.end_hour == Decimal("24")


def test_create_rejects_invalid_source() -> None:
    """ScheduleBlockCreate must reject invalid source values."""
    with pytest.raises(ValidationError):
        ScheduleBlockCreate(
            task_id=TASK_ID, date=date(2026, 5, 1),
            start_hour=Decimal("9"), end_hour=Decimal("10"),
            source="outlook",
        )


def test_create_accepts_valid_sources() -> None:
    """ScheduleBlockCreate must accept both valid source values."""
    b1 = ScheduleBlockCreate(
        task_id=TASK_ID, date=date(2026, 5, 1),
        start_hour=Decimal("9"), end_hour=Decimal("10"),
        source="manual",
    )
    assert b1.source == "manual"
    b2 = ScheduleBlockCreate(
        task_id=TASK_ID, date=date(2026, 5, 1),
        start_hour=Decimal("9"), end_hour=Decimal("10"),
        source="google_calendar",
    )
    assert b2.source == "google_calendar"


def test_create_accepts_decimal_hours() -> None:
    """ScheduleBlockCreate must accept fractional hours (e.g. 9.5 = 9:30)."""
    b = ScheduleBlockCreate(
        task_id=TASK_ID, date=date(2026, 5, 1),
        start_hour=Decimal("9.5"), end_hour=Decimal("10.75"),
    )
    assert b.start_hour == Decimal("9.5")
    assert b.end_hour == Decimal("10.75")


# ---------------------------------------------------------------------------
# ScheduleBlockUpdate
# ---------------------------------------------------------------------------


def test_update_all_fields_optional() -> None:
    """ScheduleBlockUpdate must allow empty (no fields set)."""
    u = ScheduleBlockUpdate()
    assert u.date is None
    assert u.start_hour is None
    assert u.end_hour is None
    assert u.source is None


def test_update_rejects_start_gte_end_when_both_provided() -> None:
    """ScheduleBlockUpdate must reject start_hour >= end_hour when both set."""
    with pytest.raises(ValidationError):
        ScheduleBlockUpdate(start_hour=Decimal("10"), end_hour=Decimal("9"))


def test_update_allows_partial_hour_update() -> None:
    """ScheduleBlockUpdate must allow setting only one of start/end hour."""
    u = ScheduleBlockUpdate(start_hour=Decimal("8"))
    assert u.start_hour == Decimal("8")
    assert u.end_hour is None


def test_update_rejects_invalid_source() -> None:
    """ScheduleBlockUpdate must reject invalid source values."""
    with pytest.raises(ValidationError):
        ScheduleBlockUpdate(source="outlook")


def test_update_rejects_out_of_range_hours() -> None:
    """ScheduleBlockUpdate must reject hours outside 0-24 range."""
    with pytest.raises(ValidationError):
        ScheduleBlockUpdate(start_hour=Decimal("-1"))
    with pytest.raises(ValidationError):
        ScheduleBlockUpdate(end_hour=Decimal("24.01"))


# ---------------------------------------------------------------------------
# ScheduleBlockResponse
# ---------------------------------------------------------------------------


def test_response_from_attributes() -> None:
    """ScheduleBlockResponse must support from_attributes (ORM mode)."""
    assert ScheduleBlockResponse.model_config.get("from_attributes") is True


def test_response_round_trip() -> None:
    """ScheduleBlockResponse must serialize all fields."""
    now = datetime.now(UTC)
    bid = uuid.uuid4()
    resp = ScheduleBlockResponse(
        id=bid,
        task_id=TASK_ID,
        date=date(2026, 5, 1),
        start_hour=Decimal("9.00"),
        end_hour=Decimal("10.50"),
        source="manual",
        created_at=now,
    )
    assert resp.id == bid
    assert resp.task_id == TASK_ID
    assert resp.source == "manual"
