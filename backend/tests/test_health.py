from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.core.database import get_db
from app.main import app


async def test_health_returns_ok_with_dependencies(client: AsyncClient) -> None:
    """GET /health returns 200 with database and redis status when both are up."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)

    async def _ok_db():  # type: ignore[no-untyped-def]
        yield mock_session

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = _ok_db
    try:
        with patch("app.api.health.get_redis", return_value=mock_redis):
            response = await client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["redis"] == "healthy"


async def test_health_returns_503_when_db_down(client: AsyncClient) -> None:
    """GET /health returns 503 when database is unreachable."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=ConnectionError("DB down"))

    async def _failing_db():  # type: ignore[no-untyped-def]
        yield mock_session

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = _failing_db
    try:
        with patch("app.api.health.get_redis", return_value=mock_redis):
            response = await client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    data = response.json()
    assert data["database"] == "unhealthy"


async def test_health_returns_503_when_redis_down(client: AsyncClient) -> None:
    """GET /health returns 503 when Redis is unreachable."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)

    async def _ok_db():  # type: ignore[no-untyped-def]
        yield mock_session

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("Redis down"))

    app.dependency_overrides[get_db] = _ok_db
    try:
        with patch("app.api.health.get_redis", return_value=mock_redis):
            response = await client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    data = response.json()
    assert data["redis"] == "unhealthy"
