from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures — reduce mock boilerplate across health tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_healthy_db() -> Generator[None, None, None]:
    """Override get_db with a mock session that succeeds on execute."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)

    async def _ok_db() -> AsyncGenerator[Any, None]:
        yield mock_session

    app.dependency_overrides[get_db] = _ok_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_failing_db() -> Generator[None, None, None]:
    """Override get_db with a mock session that raises on execute."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=ConnectionError("DB down"))

    async def _failing_db() -> AsyncGenerator[Any, None]:
        yield mock_session

    app.dependency_overrides[get_db] = _failing_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_healthy_redis() -> Generator[Any, None, None]:
    """Patch get_redis to return a mock that pings successfully."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    with patch("app.api.health.get_redis", return_value=mock_redis):
        yield mock_redis


@pytest.fixture
def mock_failing_redis() -> Generator[Any, None, None]:
    """Patch get_redis to return a mock that raises on ping."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("Redis down"))
    with patch("app.api.health.get_redis", return_value=mock_redis):
        yield mock_redis


@pytest.fixture
def mock_auth_user() -> Generator[None, None, None]:
    """Override get_current_user with a fake authenticated user."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


async def test_health_returns_ok_with_dependencies(
    client: AsyncClient, mock_healthy_db: None, mock_healthy_redis: Any
) -> None:
    """GET /health returns 200 with database and redis status when both are up."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["redis"] == "healthy"


async def test_health_returns_503_when_db_down(
    client: AsyncClient, mock_failing_db: None, mock_healthy_redis: Any
) -> None:
    """GET /health returns 503 when database is unreachable."""
    response = await client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unhealthy"


async def test_health_returns_503_when_redis_down(
    client: AsyncClient, mock_healthy_db: None, mock_failing_redis: Any
) -> None:
    """GET /health returns 503 when Redis is unreachable."""
    response = await client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "unhealthy"


# ---------------------------------------------------------------------------
# GET /health/detailed
# ---------------------------------------------------------------------------


async def test_health_detailed_requires_auth(
    client: AsyncClient, mock_healthy_db: None
) -> None:
    """GET /health/detailed without a token must return 401."""
    response = await client.get("/health/detailed")
    assert response.status_code == 401


async def test_health_detailed_returns_dependency_info(
    client: AsyncClient,
    mock_healthy_db: None,
    mock_healthy_redis: Any,
    mock_auth_user: None,
) -> None:
    """GET /health/detailed with valid auth returns latency and status details."""
    response = await client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"]["status"] == "healthy"
    assert data["database"]["latency_ms"] >= 0
    assert data["redis"]["status"] == "healthy"
    assert data["redis"]["latency_ms"] >= 0
    assert data["sentry_enabled"] is False
    assert data["version"]  # non-empty version string


async def test_health_detailed_returns_503_when_db_down(
    client: AsyncClient,
    mock_failing_db: None,
    mock_healthy_redis: Any,
    mock_auth_user: None,
) -> None:
    """GET /health/detailed returns 503 with degraded status when DB is down."""
    response = await client.get("/health/detailed")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"]["status"] == "unhealthy"
    assert data["redis"]["status"] == "healthy"
