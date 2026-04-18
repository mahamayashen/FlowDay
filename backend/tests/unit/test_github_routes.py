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
from app.services.github_sync import _sign_github_state

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000027")
SYNC_ID = uuid.UUID("00000000-0000-0000-0000-cccccccccccc")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "github@example.com"
    fake.name = "GitHub User"
    return fake


def _make_sync_response() -> SyncStatusResponse:
    return SyncStatusResponse(
        id=SYNC_ID,
        provider="github",
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
# GET /sync/github/auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_github_auth_returns_authorization_url(client: AsyncClient) -> None:
    """GET /sync/github/auth returns 200 with authorization_url."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.build_github_authorization_url",
            return_value="https://github.com/login/oauth/authorize?client_id=test",
        ):
            response = await client.get("/sync/github/auth")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert data["authorization_url"].startswith(
        "https://github.com/login/oauth/authorize"
    )


@pytest.mark.asyncio
async def test_github_auth_requires_authentication(client: AsyncClient) -> None:
    """GET /sync/github/auth without JWT returns 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get("/sync/github/auth")
    finally:
        _clear_overrides()

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /sync/github/callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_github_callback_success_creates_sync_record(
    client: AsyncClient,
) -> None:
    """GET /sync/github/callback with valid code returns 200."""
    _setup_overrides()
    try:
        with (
            patch(
                "app.api.sync.exchange_github_code_for_tokens",
                new_callable=AsyncMock,
                return_value={
                    "access_token": "github-access-abc",
                    "token_type": "bearer",
                },
            ),
            patch(
                "app.api.sync.store_github_tokens_in_sync_record",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.sync.get_or_create_github_sync",
                new_callable=AsyncMock,
                return_value=_make_sync_response(),
            ),
        ):
            response = await client.get(
                "/sync/github/callback",
                params={
                    "code": "github-auth-code-123",
                    "state": _sign_github_state(str(USER_ID)),
                },
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "github"


@pytest.mark.asyncio
async def test_github_callback_rejects_invalid_state(client: AsyncClient) -> None:
    """GET /sync/github/callback with wrong state returns 400."""
    _setup_overrides()
    try:
        response = await client.get(
            "/sync/github/callback",
            params={"code": "auth-code-123", "state": "wrong-state"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_github_callback_requires_authentication(client: AsyncClient) -> None:
    """GET /sync/github/callback without JWT returns 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get(
            "/sync/github/callback",
            params={"code": "auth-code-123", "state": str(USER_ID)},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 401
