from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.models.schedule_block import ScheduleBlock, ScheduleBlockSource

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TASK_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")
BLOCK_ID = uuid.UUID("00000000-0000-0000-0000-cccccccccccc")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_fake_block(**overrides: object) -> MagicMock:
    defaults = {
        "id": BLOCK_ID,
        "task_id": TASK_ID,
        "date": date(2026, 5, 1),
        "start_hour": Decimal("9.00"),
        "end_hour": Decimal("10.00"),
        "source": ScheduleBlockSource.MANUAL,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    fake = MagicMock(spec=ScheduleBlock)
    for k, v in defaults.items():
        setattr(fake, k, v)
    return fake


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
# POST /schedule-blocks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_block_returns_201(client: AsyncClient) -> None:
    """POST /schedule-blocks with valid data must return 201."""
    fake = _make_fake_block()
    _setup_overrides()
    try:
        with patch(
            "app.api.schedule_blocks.create_schedule_block",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_create.return_value = fake
            response = await client.post(
                "/schedule-blocks",
                json={
                    "task_id": str(TASK_ID),
                    "date": "2026-05-01",
                    "start_hour": "9.00",
                    "end_hour": "10.00",
                },
            )
    finally:
        _clear_overrides()

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(BLOCK_ID)


@pytest.mark.asyncio
async def test_create_block_returns_401_without_auth(client: AsyncClient) -> None:
    """POST /schedule-blocks without auth must return 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.post(
            "/schedule-blocks",
            json={
                "task_id": str(TASK_ID),
                "date": "2026-05-01",
                "start_hour": "9.00",
                "end_hour": "10.00",
            },
        )
    finally:
        _clear_overrides()
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /schedule-blocks?date=YYYY-MM-DD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_blocks_returns_200(client: AsyncClient) -> None:
    """GET /schedule-blocks?date=2026-05-01 must return 200 with list."""
    fake = _make_fake_block()
    _setup_overrides()
    try:
        with patch(
            "app.api.schedule_blocks.list_schedule_blocks",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = [fake]
            response = await client.get("/schedule-blocks?date=2026-05-01")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_blocks_requires_date_param(client: AsyncClient) -> None:
    """GET /schedule-blocks without date must return 422."""
    _setup_overrides()
    try:
        response = await client.get("/schedule-blocks")
    finally:
        _clear_overrides()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /schedule-blocks/{block_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_block_returns_200(client: AsyncClient) -> None:
    """PUT /schedule-blocks/{id} with valid data must return 200."""
    fake = _make_fake_block(start_hour=Decimal("8"), end_hour=Decimal("11"))
    _setup_overrides()
    try:
        with patch(
            "app.api.schedule_blocks.update_schedule_block",
            new_callable=AsyncMock,
        ) as mock_update:
            mock_update.return_value = fake
            response = await client.put(
                f"/schedule-blocks/{BLOCK_ID}",
                json={"start_hour": "8.00", "end_hour": "11.00"},
            )
    finally:
        _clear_overrides()

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /schedule-blocks/{block_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_block_returns_204(client: AsyncClient) -> None:
    """DELETE /schedule-blocks/{id} must return 204."""
    _setup_overrides()
    try:
        with patch(
            "app.api.schedule_blocks.delete_schedule_block",
            new_callable=AsyncMock,
        ) as mock_delete:
            mock_delete.return_value = None
            response = await client.delete(f"/schedule-blocks/{BLOCK_ID}")
    finally:
        _clear_overrides()

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_block_returns_401_without_auth(client: AsyncClient) -> None:
    """DELETE /schedule-blocks/{id} without auth must return 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        response = await client.delete(f"/schedule-blocks/{BLOCK_ID}")
    finally:
        _clear_overrides()
    assert response.status_code == 401
