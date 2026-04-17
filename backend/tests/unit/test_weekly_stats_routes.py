from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.schemas.analytics import (
    ProjectWeeklyStats,
    WeeklyStatsResponse,
    WeeklyStatsSummary,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PROJ_X = uuid.UUID("00000000-0000-0000-0000-000000001001")

WEEK_MONDAY = date(2026, 4, 13)
WEEK_SUNDAY = date(2026, 4, 19)


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_weekly_response(week_start: date = WEEK_MONDAY) -> WeeklyStatsResponse:
    return WeeklyStatsResponse(
        week_start=week_start,
        week_end=WEEK_SUNDAY,
        projects=[
            ProjectWeeklyStats(
                project_id=PROJ_X,
                project_name="Project X",
                project_color="#ff0000",
                planned_hours=4.0,
                actual_hours=3.0,
                accuracy_pct=75.0,
            )
        ],
        summary=WeeklyStatsSummary(
            total_planned_hours=4.0,
            total_actual_hours=3.0,
            average_accuracy_pct=75.0,
        ),
    )


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def _setup_overrides() -> None:
    app.dependency_overrides[get_current_user] = _make_fake_user

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /analytics/weekly-stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_weekly_stats_returns_200(client: AsyncClient) -> None:
    """GET /analytics/weekly-stats with valid week_start returns 200."""
    _setup_overrides()
    try:
        with patch(
            "app.api.analytics.get_weekly_stats",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_weekly_response()
            response = await client.get(
                "/analytics/weekly-stats", params={"week_start": "2026-04-13"}
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["week_start"] == "2026-04-13"
    assert data["week_end"] == "2026-04-19"
    assert len(data["projects"]) == 1
    assert data["projects"][0]["accuracy_pct"] == pytest.approx(75.0)


@pytest.mark.asyncio
async def test_weekly_stats_returns_401_without_auth(client: AsyncClient) -> None:
    """GET /analytics/weekly-stats without auth returns 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get(
            "/analytics/weekly-stats", params={"week_start": "2026-04-13"}
        )
    finally:
        _clear_overrides()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_weekly_stats_requires_week_start_param(client: AsyncClient) -> None:
    """GET /analytics/weekly-stats without week_start returns 422."""
    _setup_overrides()
    try:
        response = await client.get("/analytics/weekly-stats")
    finally:
        _clear_overrides()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_weekly_stats_rejects_invalid_date(client: AsyncClient) -> None:
    """GET /analytics/weekly-stats with invalid date returns 422."""
    _setup_overrides()
    try:
        response = await client.get(
            "/analytics/weekly-stats", params={"week_start": "not-a-date"}
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_weekly_stats_passes_params_to_service(client: AsyncClient) -> None:
    """Service is called with parsed week_start and correct user_id."""
    _setup_overrides()
    try:
        with patch(
            "app.api.analytics.get_weekly_stats",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_weekly_response()
            await client.get(
                "/analytics/weekly-stats", params={"week_start": "2026-04-13"}
            )
            mock_svc.assert_called_once()
            call_kwargs = mock_svc.call_args.kwargs
            assert call_kwargs["week_start"] == date(2026, 4, 13)
            assert call_kwargs["user_id"] == USER_ID
    finally:
        _clear_overrides()


@pytest.mark.asyncio
async def test_weekly_stats_response_schema(client: AsyncClient) -> None:
    """Response JSON has the expected top-level and summary keys."""
    _setup_overrides()
    try:
        with patch(
            "app.api.analytics.get_weekly_stats",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_weekly_response()
            response = await client.get(
                "/analytics/weekly-stats", params={"week_start": "2026-04-13"}
            )
    finally:
        _clear_overrides()

    data = response.json()
    assert set(data.keys()) == {"week_start", "week_end", "projects", "summary"}
    assert set(data["summary"].keys()) == {
        "total_planned_hours",
        "total_actual_hours",
        "average_accuracy_pct",
    }
    proj = data["projects"][0]
    assert set(proj.keys()) == {
        "project_id",
        "project_name",
        "project_color",
        "planned_hours",
        "actual_hours",
        "accuracy_pct",
    }
