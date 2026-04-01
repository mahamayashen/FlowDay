from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token
from app.main import app


def _make_fake_user(email: str = "test@example.com") -> MagicMock:
    fake = MagicMock()
    fake.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    fake.email = email
    fake.name = "Test User"
    fake.settings_json = {}
    fake.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    return fake


@pytest.fixture
async def auth_client() -> AsyncClient:
    """HTTP client that does NOT depend on a running database."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_auth_me_returns_current_user(auth_client: AsyncClient) -> None:
    """GET /auth/me with valid JWT must return user info."""
    email = "test@example.com"
    fake_user = _make_fake_user(email)

    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        response = await auth_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {create_access_token(subject=email)}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "google_oauth_token" not in data
    assert "github_oauth_token" not in data


@pytest.mark.asyncio
async def test_auth_me_returns_401_without_token(auth_client: AsyncClient) -> None:
    """GET /auth/me without Authorization header must return 401."""
    response = await auth_client.get("/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(
    auth_client: AsyncClient,
) -> None:
    """POST /auth/refresh with valid refresh token must return new access token."""
    refresh = create_refresh_token(subject="test@example.com")

    response = await auth_client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(
    auth_client: AsyncClient,
) -> None:
    """POST /auth/refresh with invalid token must return 401."""
    response = await auth_client.post(
        "/auth/refresh", json={"refresh_token": "bad-token"}
    )
    assert response.status_code == 401
