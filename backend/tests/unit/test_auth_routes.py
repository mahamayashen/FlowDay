from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
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
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
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
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(
    auth_client: AsyncClient,
) -> None:
    """POST /auth/refresh with valid refresh token must return new access token."""
    refresh = create_refresh_token(subject="test@example.com")
    mock_db = _mock_db_session()

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await auth_client.post(
            "/auth/refresh", json={"refresh_token": refresh}
        )
    finally:
        app.dependency_overrides.clear()

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


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(auth_client: AsyncClient) -> None:
    """POST /auth/refresh with an access token (not refresh) must return 401."""
    access = create_access_token(subject="test@example.com")

    response = await auth_client.post("/auth/refresh", json={"refresh_token": access})
    assert response.status_code == 401
    assert "not a refresh token" in response.json()["detail"]


# ---------------------------------------------------------------------------
# OAuth callback tests (mocked external HTTP)
# ---------------------------------------------------------------------------


def _mock_httpx_client(
    token_response: httpx.Response,
    userinfo_response: httpx.Response,
    emails_response: httpx.Response | None = None,
) -> AsyncMock:
    """Create a mock httpx.AsyncClient for OAuth callback tests."""
    mock_client = AsyncMock()

    async def mock_post(*args: object, **kwargs: object) -> httpx.Response:
        return token_response

    async def mock_get(url: str, **kwargs: object) -> httpx.Response:
        if "emails" in url and emails_response is not None:
            return emails_response
        return userinfo_response

    mock_client.post = mock_post
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _mock_db_session() -> AsyncMock:
    """Create a mock async DB session for OAuth callback and refresh tests."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    fake_user = _make_fake_user()
    mock_result.scalar_one.return_value = fake_user
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_db.execute.return_value = mock_result
    return mock_db


@pytest.mark.asyncio
async def test_google_callback_creates_user_and_returns_jwt(
    auth_client: AsyncClient,
) -> None:
    """GET /auth/google/callback with valid code returns JWT pair."""
    token_resp = httpx.Response(200, json={"access_token": "google-token-123"})
    userinfo_resp = httpx.Response(
        200, json={"email": "user@gmail.com", "name": "Google User"}
    )
    mock_client = _mock_httpx_client(token_resp, userinfo_resp)
    mock_db = _mock_db_session()

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with (
            patch("app.api.auth.httpx.AsyncClient", return_value=mock_client),
            patch("app.api.auth.settings") as mock_settings,
        ):
            mock_settings.GOOGLE_CLIENT_ID = "test-id"
            mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
            mock_settings.GOOGLE_REDIRECT_URI = "http://localhost/callback"

            response = await auth_client.get(
                "/auth/google/callback", params={"code": "auth-code-123"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_github_callback_creates_user_and_returns_jwt(
    auth_client: AsyncClient,
) -> None:
    """GET /auth/github/callback with valid code returns JWT pair."""
    token_resp = httpx.Response(200, json={"access_token": "github-token-456"})
    userinfo_resp = httpx.Response(
        200,
        json={
            "email": "user@github.com",
            "name": "GitHub User",
            "login": "ghuser",
        },
    )
    mock_client = _mock_httpx_client(token_resp, userinfo_resp)
    mock_db = _mock_db_session()

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with (
            patch("app.api.auth.httpx.AsyncClient", return_value=mock_client),
            patch("app.api.auth.settings") as mock_settings,
        ):
            mock_settings.GITHUB_CLIENT_ID = "test-id"
            mock_settings.GITHUB_CLIENT_SECRET = "test-secret"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"

            response = await auth_client.get(
                "/auth/github/callback", params={"code": "auth-code-456"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_oauth_callback_existing_user_updates_token(
    auth_client: AsyncClient,
) -> None:
    """Second OAuth callback for the same email should succeed (upsert)."""
    token_resp = httpx.Response(200, json={"access_token": "google-token-new"})
    userinfo_resp = httpx.Response(
        200, json={"email": "existing@gmail.com", "name": "Existing User"}
    )
    mock_client = _mock_httpx_client(token_resp, userinfo_resp)
    mock_db = _mock_db_session()

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with (
            patch("app.api.auth.httpx.AsyncClient", return_value=mock_client),
            patch("app.api.auth.settings") as mock_settings,
        ):
            mock_settings.GOOGLE_CLIENT_ID = "test-id"
            mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
            mock_settings.GOOGLE_REDIRECT_URI = "http://localhost/callback"

            response = await auth_client.get(
                "/auth/google/callback", params={"code": "auth-code-second"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    # Verify upsert was called (single execute with RETURNING)
    assert mock_db.execute.call_count >= 1
    assert mock_db.commit.call_count == 1
