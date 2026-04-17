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
    PlannedVsActualResponse,
    PlannedVsActualSummary,
    StatusTag,
    TaskComparison,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TASK_A = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_response(query_date: date = date(2026, 5, 1)) -> PlannedVsActualResponse:
    return PlannedVsActualResponse(
        date=query_date,
        tasks=[
            TaskComparison(
                task_id=TASK_A,
                task_title="Task A",
                planned_hours=2.0,
                actual_hours=2.0,
                status=StatusTag.DONE,
            ),
        ],
        summary=PlannedVsActualSummary(
            total_planned_hours=2.0,
            total_actual_hours=2.0,
            done_count=1,
            partial_count=0,
            skipped_count=0,
            unplanned_count=0,
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
# GET /analytics/planned-vs-actual
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_planned_vs_actual_returns_200(client: AsyncClient) -> None:
    """GET /analytics/planned-vs-actual with valid date returns 200."""
    _setup_overrides()
    try:
        with patch(
            "app.api.analytics.get_planned_vs_actual",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_response()
            response = await client.get(
                "/analytics/planned-vs-actual", params={"date": "2026-05-01"}
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-05-01"
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["status"] == "done"
    assert data["summary"]["done_count"] == 1


@pytest.mark.asyncio
async def test_planned_vs_actual_returns_401_without_auth(
    client: AsyncClient,
) -> None:
    """GET /analytics/planned-vs-actual without auth returns 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.get(
            "/analytics/planned-vs-actual", params={"date": "2026-05-01"}
        )
    finally:
        _clear_overrides()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_planned_vs_actual_requires_date_param(client: AsyncClient) -> None:
    """GET /analytics/planned-vs-actual without date returns 422."""
    _setup_overrides()
    try:
        response = await client.get("/analytics/planned-vs-actual")
    finally:
        _clear_overrides()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_planned_vs_actual_rejects_invalid_date(client: AsyncClient) -> None:
    """GET /analytics/planned-vs-actual with invalid date returns 422."""
    _setup_overrides()
    try:
        response = await client.get(
            "/analytics/planned-vs-actual", params={"date": "not-a-date"}
        )
    finally:
        _clear_overrides()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_planned_vs_actual_passes_date_to_service(
    client: AsyncClient,
) -> None:
    """Service is called with the parsed date from query string."""
    _setup_overrides()
    try:
        with patch(
            "app.api.analytics.get_planned_vs_actual",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_response()
            await client.get(
                "/analytics/planned-vs-actual", params={"date": "2026-05-01"}
            )
            mock_svc.assert_called_once()
            call_kwargs = mock_svc.call_args.kwargs
            assert call_kwargs["query_date"] == date(2026, 5, 1)
            assert call_kwargs["user_id"] == USER_ID
    finally:
        _clear_overrides()


@pytest.mark.asyncio
async def test_planned_vs_actual_response_schema(client: AsyncClient) -> None:
    """Response JSON has the expected top-level keys."""
    _setup_overrides()
    try:
        with patch(
            "app.api.analytics.get_planned_vs_actual",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = _make_response()
            response = await client.get(
                "/analytics/planned-vs-actual", params={"date": "2026-05-01"}
            )
    finally:
        _clear_overrides()

    data = response.json()
    assert set(data.keys()) == {"date", "tasks", "summary"}
    assert set(data["summary"].keys()) == {
        "total_planned_hours",
        "total_actual_hours",
        "done_count",
        "partial_count",
        "skipped_count",
        "unplanned_count",
    }
