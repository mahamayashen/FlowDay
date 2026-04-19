from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.main import app
from app.models.user import User


async def test_valid_jwt_returns_200(auth_client: AsyncClient, test_user: User) -> None:
    """A valid access token should allow access to /auth/me."""
    resp = await auth_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == test_user.email


async def test_expired_jwt_returns_401(
    db_session: AsyncSession, test_user: User
) -> None:
    """An expired JWT must be rejected with 401."""
    token = create_access_token(subject=test_user.email, expires_minutes=-1)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        resp = await ac.get("/auth/me")
    assert resp.status_code == 401


async def test_missing_token_returns_401(db_session: AsyncSession) -> None:
    """A request without Authorization header must return 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/auth/me")
    assert resp.status_code == 401


async def test_refresh_token_as_access_returns_401(
    db_session: AsyncSession, test_user: User
) -> None:
    """Using a refresh token as an access token must return 401."""
    token = create_refresh_token(subject=test_user.email)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        resp = await ac.get("/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/{provider}/callback — contract tests
# ---------------------------------------------------------------------------


async def test_google_callback_rejects_get(db_session: AsyncSession) -> None:
    """GET /auth/google/callback must return 405 — route is now POST only."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/auth/google/callback", params={"code": "test"})
    assert resp.status_code == 405


async def test_github_callback_rejects_get(db_session: AsyncSession) -> None:
    """GET /auth/github/callback must return 405 — route is now POST only."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/auth/github/callback", params={"code": "test"})
    assert resp.status_code == 405


async def test_google_callback_returns_501_when_not_configured(
    db_session: AsyncSession,
) -> None:
    """POST /auth/google/callback returns 501 when Google OAuth is not configured."""
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = None
        mock_settings.GOOGLE_CLIENT_SECRET = None
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/auth/google/callback", json={"code": "test-code"})
    assert resp.status_code == 501


async def test_github_callback_returns_501_when_not_configured(
    db_session: AsyncSession,
) -> None:
    """POST /auth/github/callback returns 501 when GitHub OAuth is not configured."""
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.GITHUB_CLIENT_ID = None
        mock_settings.GITHUB_CLIENT_SECRET = None
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/auth/github/callback", json={"code": "test-code"})
    assert resp.status_code == 501


async def test_google_callback_returns_401_on_bad_code(
    db_session: AsyncSession,
) -> None:
    """POST /auth/google/callback returns 401 when Google rejects the code."""
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 400

    mock_httpx_client = AsyncMock()
    mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
    mock_httpx_client.__aexit__ = AsyncMock(return_value=False)
    mock_httpx_client.post = AsyncMock(return_value=mock_token_resp)

    with (
        patch("app.api.auth.settings") as mock_settings,
        patch("app.api.auth.httpx.AsyncClient", return_value=mock_httpx_client),
    ):
        mock_settings.GOOGLE_CLIENT_ID = "gid"
        mock_settings.GOOGLE_CLIENT_SECRET = "gsecret"
        mock_settings.GOOGLE_REDIRECT_URI = "http://localhost:5173/auth/google/callback"
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/auth/google/callback", json={"code": "bad-code"})
    assert resp.status_code == 401


async def test_github_callback_returns_401_on_bad_code(
    db_session: AsyncSession,
) -> None:
    """POST /auth/github/callback returns 401 when GitHub rejects the code."""
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 400

    mock_httpx_client = AsyncMock()
    mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
    mock_httpx_client.__aexit__ = AsyncMock(return_value=False)
    mock_httpx_client.post = AsyncMock(return_value=mock_token_resp)

    with (
        patch("app.api.auth.settings") as mock_settings,
        patch("app.api.auth.httpx.AsyncClient", return_value=mock_httpx_client),
    ):
        mock_settings.GITHUB_CLIENT_ID = "ghid"
        mock_settings.GITHUB_CLIENT_SECRET = "ghsecret"
        mock_settings.GITHUB_REDIRECT_URI = "http://localhost:5173/auth/github/callback"
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/auth/github/callback", json={"code": "bad-code"})
    assert resp.status_code == 401
