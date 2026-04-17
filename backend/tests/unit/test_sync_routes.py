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

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SYNC_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_sync_response(provider: str = "github") -> SyncStatusResponse:
    return SyncStatusResponse(
        id=SYNC_ID,
        provider=provider,
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
# GET /sync/status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_sync_status_returns_200(client: AsyncClient) -> None:
    """GET /sync/status returns 200 with list of sync connections."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.get_sync_status",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = [_make_sync_response()]
            response = await client.get("/sync/status")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["provider"] == "github"


@pytest.mark.asyncio
async def test_get_sync_status_returns_401_without_auth(client: AsyncClient) -> None:
    """GET /sync/status without auth returns 401."""
    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get("/sync/status")
    finally:
        _clear_overrides()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_sync_status_returns_empty_list(client: AsyncClient) -> None:
    """GET /sync/status returns 200 with empty list when no connections."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.get_sync_status",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = []
            response = await client.get("/sync/status")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /sync/{provider}/trigger
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trigger_sync_returns_200(client: AsyncClient) -> None:
    """POST /sync/github/trigger returns 200 with updated sync record."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.trigger_sync",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_sync_response("github")
            response = await client.post("/sync/github/trigger")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["provider"] == "github"


@pytest.mark.asyncio
async def test_trigger_sync_returns_401_without_auth(client: AsyncClient) -> None:
    """POST /sync/github/trigger without auth returns 401."""
    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.post("/sync/github/trigger")
    finally:
        _clear_overrides()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_trigger_sync_returns_404_no_sync_record(client: AsyncClient) -> None:
    """POST /sync/github/trigger returns 404 when no sync record found."""
    from fastapi import HTTPException

    _setup_overrides()
    try:
        with patch(
            "app.api.sync.trigger_sync",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = HTTPException(
                status_code=404, detail="Sync connection not found"
            )
            response = await client.post("/sync/github/trigger")
    finally:
        _clear_overrides()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_sync_returns_501_unknown_provider(client: AsyncClient) -> None:
    """POST /sync/github/trigger returns 501 when provider not implemented."""
    from fastapi import HTTPException

    _setup_overrides()
    try:
        with patch(
            "app.api.sync.trigger_sync",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = HTTPException(
                status_code=501, detail="Provider not implemented"
            )
            response = await client.post("/sync/github/trigger")
    finally:
        _clear_overrides()

    assert response.status_code == 501


@pytest.mark.asyncio
async def test_trigger_sync_passes_provider_to_service(client: AsyncClient) -> None:
    """POST /sync/{provider}/trigger passes provider string to service."""
    _setup_overrides()
    try:
        with patch(
            "app.api.sync.trigger_sync",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_sync_response("google_calendar")
            await client.post("/sync/google_calendar/trigger")
            mock_svc.assert_called_once()
            call_kwargs = mock_svc.call_args.kwargs
            assert call_kwargs["provider"] == "google_calendar"
            assert call_kwargs["user_id"] == USER_ID
    finally:
        _clear_overrides()
