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
from app.models.time_entry import TimeEntry

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TASK_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")
ENTRY_ID = uuid.UUID("00000000-0000-0000-0000-cccccccccccc")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_fake_entry(**overrides: object) -> MagicMock:
    defaults: dict[str, object] = {
        "id": ENTRY_ID,
        "task_id": TASK_ID,
        "started_at": datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
        "ended_at": None,
        "duration_seconds": None,
        "created_at": datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    fake = MagicMock(spec=TimeEntry)
    for k, v in defaults.items():
        setattr(fake, k, v)
    return fake


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
# POST /time-entries/start
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_timer_returns_201(client: AsyncClient) -> None:
    """POST /time-entries/start with valid data must return 201."""
    fake = _make_fake_entry()
    _setup_overrides()
    try:
        with patch(
            "app.api.time_entries.start_timer",
            new_callable=AsyncMock,
        ) as mock_start:
            mock_start.return_value = fake
            response = await client.post(
                "/time-entries/start",
                json={"task_id": str(TASK_ID)},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(ENTRY_ID)


@pytest.mark.asyncio
async def test_start_timer_returns_401_without_auth(client: AsyncClient) -> None:
    """POST /time-entries/start without auth must return 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.post(
            "/time-entries/start",
            json={"task_id": str(TASK_ID)},
        )
    finally:
        _clear_overrides()
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /time-entries/{entry_id}/stop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_timer_returns_200(client: AsyncClient) -> None:
    """POST /time-entries/{id}/stop must return 200."""
    fake = _make_fake_entry(
        ended_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        duration_seconds=3600,
    )
    _setup_overrides()
    try:
        with patch(
            "app.api.time_entries.stop_timer",
            new_callable=AsyncMock,
        ) as mock_stop:
            mock_stop.return_value = fake
            response = await client.post(f"/time-entries/{ENTRY_ID}/stop")
    finally:
        _clear_overrides()

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /time-entries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_entries_returns_200(client: AsyncClient) -> None:
    """GET /time-entries?task_id=... must return 200 with list."""
    fake = _make_fake_entry()
    _setup_overrides()
    try:
        with patch(
            "app.api.time_entries.list_time_entries",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = [fake]
            response = await client.get(
                f"/time-entries?task_id={TASK_ID}"
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_entries_accepts_date_filter(client: AsyncClient) -> None:
    """GET /time-entries?date=2026-05-01 must return 200."""
    _setup_overrides()
    try:
        with patch(
            "app.api.time_entries.list_time_entries",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = []
            response = await client.get("/time-entries?date=2026-05-01")
    finally:
        _clear_overrides()

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_entries_works_without_filters(client: AsyncClient) -> None:
    """GET /time-entries without filters must return 200."""
    _setup_overrides()
    try:
        with patch(
            "app.api.time_entries.list_time_entries",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = []
            response = await client.get("/time-entries")
    finally:
        _clear_overrides()

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /time-entries/{entry_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_entry_returns_204(client: AsyncClient) -> None:
    """DELETE /time-entries/{id} must return 204."""
    _setup_overrides()
    try:
        with patch(
            "app.api.time_entries.delete_time_entry",
            new_callable=AsyncMock,
        ) as mock_delete:
            mock_delete.return_value = None
            response = await client.delete(f"/time-entries/{ENTRY_ID}")
    finally:
        _clear_overrides()

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_entry_returns_401_without_auth(client: AsyncClient) -> None:
    """DELETE /time-entries/{id} without auth must return 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.delete(f"/time-entries/{ENTRY_ID}")
    finally:
        _clear_overrides()
    assert response.status_code == 401
