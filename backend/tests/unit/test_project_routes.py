from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.models.project import Project, ProjectStatus

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_fake_project(**overrides: object) -> MagicMock:
    defaults = {
        "id": PROJECT_ID,
        "user_id": USER_ID,
        "name": "Test Project",
        "color": "#FF0000",
        "client_name": None,
        "hourly_rate": None,
        "status": ProjectStatus.ACTIVE,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    fake = MagicMock(spec=Project)
    for k, v in defaults.items():
        setattr(fake, k, v)
    return fake


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def _override_auth() -> None:
    app.dependency_overrides[get_current_user] = _make_fake_user


def _override_db(mock_db: AsyncMock) -> None:
    async def override() -> AsyncMock:  # type: ignore[misc]
        yield mock_db

    app.dependency_overrides[get_db] = override


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /projects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_project_returns_201(client: AsyncClient) -> None:
    """POST /projects with valid data must return 201."""
    fake = _make_fake_project()
    _override_auth()
    try:
        with patch(
            "app.api.projects.create_project", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = fake
            response = await client.post(
                "/projects",
                json={"name": "Work", "color": "#00FF00"},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] == str(PROJECT_ID)


@pytest.mark.asyncio
async def test_create_project_returns_401_without_auth(
    client: AsyncClient,
) -> None:
    """POST /projects without auth must return 401."""
    response = await client.post(
        "/projects", json={"name": "Work", "color": "#FF0000"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /projects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_projects_returns_200(client: AsyncClient) -> None:
    """GET /projects must return 200 with list of projects."""
    fake1 = _make_fake_project(name="P1")
    fake2 = _make_fake_project(name="P2")
    _override_auth()
    try:
        with patch(
            "app.api.projects.list_projects", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [fake1, fake2]
            response = await client.get("/projects")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /projects/{project_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_project_returns_200(client: AsyncClient) -> None:
    """GET /projects/{id} must return 200 for existing project."""
    fake = _make_fake_project()
    _override_auth()
    try:
        with patch(
            "app.api.projects.get_project", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = fake
            response = await client.get(f"/projects/{PROJECT_ID}")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["id"] == str(PROJECT_ID)


# ---------------------------------------------------------------------------
# PATCH /projects/{project_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_project_returns_200(client: AsyncClient) -> None:
    """PATCH /projects/{id} with valid data must return 200."""
    fake = _make_fake_project(name="Updated")
    _override_auth()
    try:
        with patch(
            "app.api.projects.update_project", new_callable=AsyncMock
        ) as mock_update:
            mock_update.return_value = fake
            response = await client.patch(
                f"/projects/{PROJECT_ID}",
                json={"name": "Updated"},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_project_returns_204(client: AsyncClient) -> None:
    """DELETE /projects/{id} must return 204 No Content."""
    _override_auth()
    try:
        with patch(
            "app.api.projects.delete_project", new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = None
            response = await client.delete(f"/projects/{PROJECT_ID}")
    finally:
        _clear_overrides()

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_project_returns_401_without_auth(
    client: AsyncClient,
) -> None:
    """DELETE /projects/{id} without auth must return 401."""
    response = await client.delete(f"/projects/{PROJECT_ID}")
    assert response.status_code == 401
