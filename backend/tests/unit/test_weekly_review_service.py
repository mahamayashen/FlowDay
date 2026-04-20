from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.weekly_review import ReviewStatus, WeeklyReview
from app.services.weekly_review_service import _align_to_monday, get_or_create_review

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Cycle 3 — _align_to_monday helper
# ---------------------------------------------------------------------------


def test_align_to_monday_already_monday() -> None:
    assert _align_to_monday(date(2026, 4, 13)) == date(2026, 4, 13)


def test_align_to_monday_from_wednesday() -> None:
    assert _align_to_monday(date(2026, 4, 15)) == date(2026, 4, 13)


def test_align_to_monday_from_sunday() -> None:
    assert _align_to_monday(date(2026, 4, 19)) == date(2026, 4, 13)


# ---------------------------------------------------------------------------
# Cycle 3 — get_or_create_review
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_or_create_review_creates_new() -> None:
    """When no review exists, a new one is created with status=pending."""
    db = MagicMock()
    # Simulate SELECT returning no result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    week_start = date(2026, 4, 13)
    review = await get_or_create_review(db, USER_ID, week_start)

    assert review.user_id == USER_ID
    assert review.week_start == week_start
    assert review.status == ReviewStatus.PENDING
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_review_returns_existing() -> None:
    """When a review exists, the existing one is returned without creating a new one."""
    existing = WeeklyReview(
        user_id=USER_ID,
        week_start=date(2026, 4, 13),
        raw_data_json={},
        status=ReviewStatus.COMPLETE,
    )
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    db.execute = AsyncMock(return_value=mock_result)

    review = await get_or_create_review(db, USER_ID, date(2026, 4, 13))

    assert review is existing
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_review_normalizes_week_start_to_monday() -> None:
    """Input date mid-week is clamped to Monday before lookup and storage."""
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    # Wednesday → should store as Monday 2026-04-13
    review = await get_or_create_review(db, USER_ID, date(2026, 4, 15))

    assert review.week_start == date(2026, 4, 13)
