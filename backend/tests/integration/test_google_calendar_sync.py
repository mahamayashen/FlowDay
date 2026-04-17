from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.models.external_sync import ExternalSync
from app.models.schedule_block import ScheduleBlock
from app.models.user import User


@pytest.mark.asyncio
async def test_callback_creates_external_sync_record(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """GET /sync/google-calendar/callback creates an ExternalSync row with encrypted tokens."""
    fake_tokens = {
        "access_token": "integration-access",
        "refresh_token": "integration-refresh",
        "expires_in": 3600,
    }

    with patch(
        "app.api.sync.exchange_code_for_tokens",
        new_callable=AsyncMock,
        return_value=fake_tokens,
    ):
        resp = await auth_client.get(
            "/sync/google-calendar/callback",
            params={"code": "auth-code", "state": str(test_user.id)},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "google_calendar"
    assert data["status"] == "active"

    # Verify DB row exists with encrypted tokens
    result = await db_session.execute(
        select(ExternalSync).where(
            ExternalSync.user_id == test_user.id,
            ExternalSync.provider == "google_calendar",
        )
    )
    record = result.scalar_one_or_none()
    assert record is not None
    config = record.sync_config_json
    assert "encrypted_access_token" in config
    assert "encrypted_refresh_token" in config
    assert decrypt_oauth_token(config["encrypted_access_token"]) == "integration-access"
    assert decrypt_oauth_token(config["encrypted_refresh_token"]) == "integration-refresh"


@pytest.mark.asyncio
async def test_sync_trigger_creates_schedule_blocks(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """POST /sync/google_calendar/trigger creates ScheduleBlock rows for fetched events."""
    # Pre-insert ExternalSync record with valid tokens
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    sync_record = ExternalSync(
        user_id=test_user.id,
        provider="google_calendar",
        status="active",
        sync_config_json={
            "encrypted_access_token": encrypt_oauth_token("tok"),
            "encrypted_refresh_token": encrypt_oauth_token("ref"),
            "token_expiry": future,
        },
    )
    db_session.add(sync_record)
    await db_session.flush()

    fake_events = [
        {
            "id": "evt-integration-1",
            "summary": "Integration Test Meeting",
            "start": {"dateTime": "2026-04-20T10:00:00+00:00"},
            "end": {"dateTime": "2026-04-20T11:00:00+00:00"},
        }
    ]

    with patch(
        "app.services.google_calendar_provider.fetch_calendar_events",
        new_callable=AsyncMock,
        return_value=fake_events,
    ):
        resp = await auth_client.post("/sync/google_calendar/trigger")

    assert resp.status_code == 200

    # Verify ScheduleBlock was created
    result = await db_session.execute(select(ScheduleBlock))
    blocks = result.scalars().all()
    google_blocks = [b for b in blocks if b.source == "google_calendar"]
    assert len(google_blocks) >= 1
    assert google_blocks[0].start_hour == 10
    assert google_blocks[0].end_hour == 11


@pytest.mark.asyncio
async def test_callback_rejected_with_wrong_state(
    auth_client: AsyncClient,
    test_user: User,
) -> None:
    """GET /sync/google-calendar/callback with wrong state returns 400."""
    resp = await auth_client.get(
        "/sync/google-calendar/callback",
        params={"code": "code", "state": "wrong-user-id"},
    )
    assert resp.status_code == 400
