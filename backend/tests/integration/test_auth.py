from __future__ import annotations

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


async def test_expired_jwt_returns_401(db_session: AsyncSession) -> None:
    """An expired JWT must be rejected with 401."""
    token = create_access_token(subject="expired@example.com", expires_minutes=-1)
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
