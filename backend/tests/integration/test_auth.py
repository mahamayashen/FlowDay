from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token


@pytest.mark.asyncio
async def test_auth_me_returns_current_user(client: AsyncClient) -> None:
    """GET /auth/me with valid JWT must return user info."""
    email = "test@example.com"
    token = create_access_token(subject=email)

    # Mock get_current_user to return a fake user
    fake_user = MagicMock()
    fake_user.id = "00000000-0000-0000-0000-000000000001"
    fake_user.email = email
    fake_user.name = "Test User"
    fake_user.settings_json = {}
    fake_user.created_at = "2026-01-01T00:00:00+00:00"

    with patch("app.api.auth.get_current_user", return_value=fake_user):
        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "google_oauth_token" not in data
    assert "github_oauth_token" not in data


@pytest.mark.asyncio
async def test_auth_me_returns_401_without_token(client: AsyncClient) -> None:
    """GET /auth/me without Authorization header must return 401."""
    response = await client.get("/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client: AsyncClient) -> None:
    """POST /auth/refresh with valid refresh token must return new access token."""
    refresh = create_refresh_token(subject="test@example.com")

    response = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(client: AsyncClient) -> None:
    """POST /auth/refresh with invalid token must return 401."""
    response = await client.post("/auth/refresh", json={"refresh_token": "bad-token"})
    assert response.status_code == 401
