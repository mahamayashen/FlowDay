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
    assert data["status"] == "degraded"
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
    assert data["status"] == "degraded"
    assert data["redis"] == "unhealthy"


async def test_health_detailed_requires_auth(client: AsyncClient) -> None:
    """GET /health/detailed without a token must return 401."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)

    async def _ok_db():  # type: ignore[no-untyped-def]
        yield mock_session

    app.dependency_overrides[get_db] = _ok_db
    try:
        response = await client.get("/health/detailed")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 401


async def test_health_detailed_returns_dependency_info(client: AsyncClient) -> None:
    """GET /health/detailed with valid auth returns latency and status details."""
    from app.core.deps import get_current_user

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)

    async def _ok_db():  # type: ignore[no-untyped-def]
        yield mock_session

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = _ok_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        with patch("app.api.health.get_redis", return_value=mock_redis):
            response = await client.get("/health/detailed")
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"]["status"] == "healthy"
    assert data["database"]["latency_ms"] >= 0
    assert data["redis"]["status"] == "healthy"
    assert data["redis"]["latency_ms"] >= 0
    assert data["sentry_enabled"] is False
    assert data["version"] == "0.1.0"


async def test_health_detailed_returns_503_when_db_down(client: AsyncClient) -> None:
    """GET /health/detailed returns 503 with degraded status when DB is down."""
    from app.core.deps import get_current_user

    mock_user = MagicMock()

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=ConnectionError("DB down"))

    async def _failing_db():  # type: ignore[no-untyped-def]
        yield mock_session

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = _failing_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        with patch("app.api.health.get_redis", return_value=mock_redis):
            response = await client.get("/health/detailed")
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"]["status"] == "unhealthy"
    assert data["redis"]["status"] == "healthy"
