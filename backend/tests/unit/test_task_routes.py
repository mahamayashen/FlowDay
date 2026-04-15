from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.models.task import Task

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")
TASK_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")

BASE_URL = f"/projects/{PROJECT_ID}/tasks"


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_fake_task(**overrides: object) -> MagicMock:
    defaults = {
        "id": TASK_ID,
        "project_id": PROJECT_ID,
        "title": "Test Task",
        "description": None,
        "estimate_minutes": None,
        "priority": "medium",
        "status": "todo",
        "due_date": None,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "completed_at": None,
    }
    defaults.update(overrides)
    fake = MagicMock(spec=Task)
    for k, v in defaults.items():
        setattr(fake, k, v)
    return fake


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def _setup_overrides() -> None:
    """Override auth and DB dependencies for route tests."""
    app.dependency_overrides[get_current_user] = _make_fake_user

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_task_returns_201(client: AsyncClient) -> None:
    """POST /projects/{pid}/tasks with valid data must return 201."""
    fake = _make_fake_task()
    _setup_overrides()
    try:
        with patch("app.api.tasks.create_task", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = fake
            response = await client.post(
                BASE_URL,
                json={"title": "Write tests"},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["id"] == str(TASK_ID)


@pytest.mark.asyncio
async def test_create_task_returns_401_without_auth(
    client: AsyncClient,
) -> None:
    """POST /projects/{pid}/tasks without auth must return 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.post(BASE_URL, json={"title": "Work"})
    finally:
        _clear_overrides()
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tasks_returns_200(client: AsyncClient) -> None:
    """GET /projects/{pid}/tasks must return 200 with list of tasks."""
    fake1 = _make_fake_task(title="T1")
    fake2 = _make_fake_task(title="T2")
    _setup_overrides()
    try:
        with patch("app.api.tasks.list_tasks", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [fake1, fake2]
            response = await client.get(BASE_URL)
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/tasks/{task_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_task_returns_200(client: AsyncClient) -> None:
    """GET /projects/{pid}/tasks/{tid} must return 200 for existing task."""
    fake = _make_fake_task()
    _setup_overrides()
    try:
        with patch("app.api.tasks.get_task", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = fake
            response = await client.get(f"{BASE_URL}/{TASK_ID}")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["id"] == str(TASK_ID)


# ---------------------------------------------------------------------------
# PATCH /projects/{project_id}/tasks/{task_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_task_returns_200(client: AsyncClient) -> None:
    """PATCH /projects/{pid}/tasks/{tid} with valid data must return 200."""
    fake = _make_fake_task(title="Updated")
    _setup_overrides()
    try:
        with patch("app.api.tasks.update_task", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = fake
            response = await client.patch(
                f"{BASE_URL}/{TASK_ID}",
                json={"title": "Updated"},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}/tasks/{task_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_task_returns_204(client: AsyncClient) -> None:
    """DELETE /projects/{pid}/tasks/{tid} must return 204 No Content."""
    _setup_overrides()
    try:
        with patch("app.api.tasks.delete_task", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = None
            response = await client.delete(f"{BASE_URL}/{TASK_ID}")
    finally:
        _clear_overrides()

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_task_returns_401_without_auth(
    client: AsyncClient,
) -> None:
    """DELETE /projects/{pid}/tasks/{tid} without auth must return 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.delete(f"{BASE_URL}/{TASK_ID}")
    finally:
        _clear_overrides()
    assert response.status_code == 401
