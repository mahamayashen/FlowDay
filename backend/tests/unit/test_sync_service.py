from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.sync_service import get_sync_status, trigger_sync

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SYNC_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")


def _make_fake_sync(provider: str = "github", status: str = "active") -> MagicMock:
    fake = MagicMock()
    fake.id = SYNC_ID
    fake.user_id = USER_ID
    fake.provider = provider
    fake.status = status
    fake.last_synced_at = None
    fake.sync_config_json = {}
    return fake


def _mock_db_returning(rows: list[MagicMock]) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = rows
    result.scalars.return_value = scalars
    db.execute.return_value = result
    return db


# ---------------------------------------------------------------------------
# get_sync_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_sync_status_returns_list() -> None:
    """get_sync_status returns all ExternalSync records for the user."""
    records = [_make_fake_sync("github"), _make_fake_sync("google_calendar")]
    db = _mock_db_returning(records)
    result = await get_sync_status(db, USER_ID)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_sync_status_returns_empty() -> None:
    """get_sync_status returns an empty list when user has no sync connections."""
    db = _mock_db_returning([])
    result = await get_sync_status(db, USER_ID)
    assert result == []


@pytest.mark.asyncio
async def test_get_sync_status_filters_by_user_id() -> None:
    """get_sync_status query must filter by user_id."""
    db = _mock_db_returning([])
    await get_sync_status(db, USER_ID)
    stmt = db.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert USER_ID.hex in compiled


# ---------------------------------------------------------------------------
# trigger_sync
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trigger_sync_raises_404_when_no_record() -> None:
    """trigger_sync raises HTTP 404 when no ExternalSync record exists."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await trigger_sync(db, USER_ID, "github")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_trigger_sync_raises_501_when_provider_not_registered() -> None:
    """trigger_sync raises HTTP 501 when provider is not in registry."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = _make_fake_sync("github")
    db.execute.return_value = result

    with patch("app.services.sync_service.provider_registry") as mock_registry:
        mock_registry.get.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await trigger_sync(db, USER_ID, "github")
    assert exc_info.value.status_code == 501


@pytest.mark.asyncio
async def test_trigger_sync_calls_provider_sync() -> None:
    """trigger_sync calls the registered provider's sync() method."""
    fake_record = _make_fake_sync("github")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = fake_record
    db.execute.return_value = result

    mock_provider_instance = AsyncMock()
    mock_provider_cls = MagicMock(return_value=mock_provider_instance)

    with patch("app.services.sync_service.provider_registry") as mock_registry:
        mock_registry.get.return_value = mock_provider_cls
        await trigger_sync(db, USER_ID, "github")

    mock_provider_instance.sync.assert_called_once_with(db, fake_record)


@pytest.mark.asyncio
async def test_trigger_sync_updates_last_synced_at() -> None:
    """trigger_sync sets last_synced_at and commits on success."""
    fake_record = _make_fake_sync("github")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = fake_record
    db.execute.return_value = result

    mock_provider_instance = AsyncMock()
    mock_provider_cls = MagicMock(return_value=mock_provider_instance)

    with patch("app.services.sync_service.provider_registry") as mock_registry:
        mock_registry.get.return_value = mock_provider_cls
        await trigger_sync(db, USER_ID, "github")

    assert fake_record.last_synced_at is not None
    assert fake_record.status == "active"
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_sync_sets_error_on_failure() -> None:
    """trigger_sync sets status to 'error' and commits when provider raises."""
    fake_record = _make_fake_sync("github")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = fake_record
    db.execute.return_value = result

    mock_provider_instance = AsyncMock()
    mock_provider_instance.sync.side_effect = RuntimeError("sync failed")
    mock_provider_cls = MagicMock(return_value=mock_provider_instance)

    with patch("app.services.sync_service.provider_registry") as mock_registry:
        mock_registry.get.return_value = mock_provider_cls
        await trigger_sync(db, USER_ID, "github")

    assert fake_record.status == "error"
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_sync_reraises_http_exception() -> None:
    """trigger_sync does not swallow HTTPException raised by the provider."""
    fake_record = _make_fake_sync("github")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = fake_record
    db.execute.return_value = result

    mock_provider_instance = AsyncMock()
    mock_provider_instance.sync.side_effect = HTTPException(
        status_code=401, detail="OAuth token expired"
    )
    mock_provider_cls = MagicMock(return_value=mock_provider_instance)

    with patch("app.services.sync_service.provider_registry") as mock_registry:
        mock_registry.get.return_value = mock_provider_cls
        with pytest.raises(HTTPException) as exc_info:
            await trigger_sync(db, USER_ID, "github")

    assert exc_info.value.status_code == 401
    assert fake_record.status != "error"
