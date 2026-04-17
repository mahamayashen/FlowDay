from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.sync import SyncStatusResponse


def test_sync_status_response_from_attributes() -> None:
    """SyncStatusResponse must have from_attributes=True for ORM conversion."""
    assert SyncStatusResponse.model_config.get("from_attributes") is True


def test_sync_status_response_round_trip() -> None:
    """SyncStatusResponse instantiates correctly with all fields."""
    sync_id = uuid.uuid4()
    now = datetime.now(UTC)
    resp = SyncStatusResponse(
        id=sync_id,
        provider="github",
        status="active",
        last_synced_at=now,
        sync_config_json={},
        created_at=now,
    )
    assert resp.id == sync_id
    assert resp.provider == "github"
    assert resp.status == "active"
    assert resp.last_synced_at == now
    assert resp.sync_config_json == {}
    assert resp.created_at == now


def test_sync_status_response_allows_null_last_synced_at() -> None:
    """SyncStatusResponse must accept last_synced_at=None."""
    now = datetime.now(UTC)
    resp = SyncStatusResponse(
        id=uuid.uuid4(),
        provider="google_calendar",
        status="active",
        last_synced_at=None,
        sync_config_json={},
        created_at=now,
    )
    assert resp.last_synced_at is None


def test_sync_status_response_rejects_missing_required_fields() -> None:
    """SyncStatusResponse raises ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        SyncStatusResponse(provider="github")  # type: ignore[call-arg]
