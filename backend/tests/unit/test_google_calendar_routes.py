from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.schemas.sync import SyncStatusResponse

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
SYNC_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "gcal@example.com"
    fake.name = "GCal User"
    return fake


def _make_sync_response() -> SyncStatusResponse:
    return SyncStatusResponse(
        id=SYNC_ID,
        provider="google_calendar",
        status="active",
        last_synced_at=None,
        sync_config_json={},
        created_at=datetime.now(UTC),
    )


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def _setup_overrides() -> None:
    app.dependency_overrides[get_current_user] = _make_fake_user

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /sync/google-calendar/auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_returns_authorization_url(client: AsyncClient) -> None:
    """GET /sync/google-calendar/auth returns 200 with authorization_url."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.build_authorization_url",
            return_value="https://accounts.google.com/o/oauth2/v2/auth?scope=calendar",
        ):
            response = await client.get("/sync/google-calendar/auth")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert data["authorization_url"].startswith("https://accounts.google.com")


@pytest.mark.asyncio
async def test_auth_requires_authentication(client: AsyncClient) -> None:
    """GET /sync/google-calendar/auth without JWT returns 401."""
    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get("/sync/google-calendar/auth")
    finally:
        _clear_overrides()

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /sync/google-calendar/callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_callback_success_creates_sync_record(client: AsyncClient) -> None:
    """GET /sync/google-calendar/callback with valid code returns 200 and sync record."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.exchange_code_for_tokens",
            new_callable=AsyncMock,
            return_value={
                "access_token": "access-abc",
                "refresh_token": "refresh-xyz",
                "expires_in": 3600,
            },
        ), patch(
            "app.api.sync.store_tokens_in_sync_record",
            new_callable=AsyncMock,
        ), patch(
            "app.api.sync.get_or_create_google_calendar_sync",
            new_callable=AsyncMock,
            return_value=_make_sync_response(),
        ):
            response = await client.get(
                "/sync/google-calendar/callback",
                params={"code": "auth-code-123", "state": str(USER_ID)},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "google_calendar"


@pytest.mark.asyncio
async def test_callback_rejects_invalid_state(client: AsyncClient) -> None:
    """GET /sync/google-calendar/callback with wrong state returns 400."""
    _setup_overrides()
    try:
        response = await client.get(
            "/sync/google-calendar/callback",
            params={"code": "auth-code-123", "state": "wrong-state"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_callback_requires_authentication(client: AsyncClient) -> None:
    """GET /sync/google-calendar/callback without JWT returns 401."""
    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get(
            "/sync/google-calendar/callback",
            params={"code": "auth-code-123", "state": str(USER_ID)},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 401
