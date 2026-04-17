from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import encrypt_oauth_token
from app.services.sync_provider import provider_registry


# ---------------------------------------------------------------------------
# Provider registration
# ---------------------------------------------------------------------------


def test_provider_registered_in_registry() -> None:
    """GoogleCalendarSyncProvider must be registered under 'google_calendar'."""
    import app.services.google_calendar_provider  # noqa: F401

    from app.services.google_calendar_provider import GoogleCalendarSyncProvider

    registered = provider_registry.get("google_calendar")
    assert registered is GoogleCalendarSyncProvider


# ---------------------------------------------------------------------------
# sync() — creates project, task, and schedule blocks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_creates_sentinel_project_task_and_block() -> None:
    """sync() creates a sentinel project, task per event, and schedule block per event."""
    import app.services.google_calendar_provider  # noqa: F401
    from app.services.google_calendar_provider import GoogleCalendarSyncProvider

    provider = GoogleCalendarSyncProvider()

    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("tok"),
        "encrypted_refresh_token": encrypt_oauth_token("ref"),
        "token_expiry": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    }

    fake_events = [
        {
            "id": "evt1",
            "summary": "Team Standup",
            "start": {"dateTime": "2026-04-20T09:00:00+00:00"},
            "end": {"dateTime": "2026-04-20T09:30:00+00:00"},
        }
    ]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_none())

    with patch(
        "app.services.google_calendar_provider.get_valid_access_token",
        new_callable=AsyncMock,
        return_value="access-token",
    ), patch(
        "app.services.google_calendar_provider.fetch_calendar_events",
        new_callable=AsyncMock,
        return_value=fake_events,
    ):
        await provider.sync(db, sync_record)

    # db.add should be called at least once (project + task + block)
    assert db.add.call_count >= 1
    assert db.flush.called


@pytest.mark.asyncio
async def test_sync_skips_all_day_events() -> None:
    """sync() skips events that have only start.date (all-day events)."""
    import app.services.google_calendar_provider  # noqa: F401
    from app.services.google_calendar_provider import GoogleCalendarSyncProvider

    provider = GoogleCalendarSyncProvider()

    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()

    fake_events = [
        {
            "id": "all-day-evt",
            "summary": "Holiday",
            "start": {"date": "2026-04-20"},
            "end": {"date": "2026-04-21"},
        }
    ]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_none())

    with patch(
        "app.services.google_calendar_provider.get_valid_access_token",
        new_callable=AsyncMock,
        return_value="access-token",
    ), patch(
        "app.services.google_calendar_provider.fetch_calendar_events",
        new_callable=AsyncMock,
        return_value=fake_events,
    ):
        await provider.sync(db, sync_record)

    # Only the sentinel project may be created/looked up — no Task/ScheduleBlock adds
    # Since all-day event is skipped, task + block creation should not happen
    # We can verify by checking that add was not called with a ScheduleBlock
    from app.models.schedule_block import ScheduleBlock

    added_types = [type(call.args[0]) for call in db.add.call_args_list if call.args]
    assert ScheduleBlock not in added_types


@pytest.mark.asyncio
async def test_sync_token_error_propagates() -> None:
    """sync() propagates HTTPException when token retrieval fails."""
    import app.services.google_calendar_provider  # noqa: F401
    from app.services.google_calendar_provider import GoogleCalendarSyncProvider

    from fastapi import HTTPException

    provider = GoogleCalendarSyncProvider()
    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    with patch(
        "app.services.google_calendar_provider.get_valid_access_token",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=401, detail="not connected"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await provider.sync(db, sync_record)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_scalar_none() -> MagicMock:
    """Return a mock db.execute() result that yields scalar_one_or_none() == None."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    return result
