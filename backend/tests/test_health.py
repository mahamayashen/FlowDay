from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_health_returns_ok_with_dependencies(client: AsyncClient) -> None:
    """GET /health returns 200 with database and redis status when both are up."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["redis"] == "healthy"


async def test_health_returns_503_when_db_down(client: AsyncClient) -> None:
    """GET /health returns 503 when database is unreachable."""
    with patch(
        "app.api.health.get_db",
        return_value=_failing_db_gen(),
    ):
        response = await client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["database"] == "unhealthy"


async def test_health_returns_503_when_redis_down(client: AsyncClient) -> None:
    """GET /health returns 503 when Redis is unreachable."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=ConnectionError("Redis down"))
    with patch("app.api.health.get_redis", return_value=mock_redis):
        response = await client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["redis"] == "unhealthy"


async def _failing_db_gen():  # type: ignore[no-untyped-def]
    """Async generator that simulates a DB failure."""
    raise ConnectionError("DB down")
    yield  # noqa: RUF027 — make this an async generator
