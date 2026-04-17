from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.models.external_sync import ExternalSync, SyncProvider, SyncStatus


def test_external_sync_table_name() -> None:
    """ExternalSync.__tablename__ must be 'external_syncs'."""
    assert ExternalSync.__tablename__ == "external_syncs"


def test_external_sync_has_required_columns() -> None:
    """ExternalSync model must have all columns defined in DATA_MODEL.md."""
    columns = {c.name for c in inspect(ExternalSync).columns}
    expected = {
        "id",
        "user_id",
        "provider",
        "last_synced_at",
        "sync_config_json",
        "status",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_external_sync_id_is_uuid() -> None:
    """ExternalSync.id column type must be UUID."""
    col = inspect(ExternalSync).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_external_sync_user_id_is_foreign_key() -> None:
    """ExternalSync.user_id must reference users.id."""
    col = inspect(ExternalSync).columns["user_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "users.id" in fk_targets


def test_external_sync_user_id_not_nullable() -> None:
    """ExternalSync.user_id must be NOT NULL."""
    col = inspect(ExternalSync).columns["user_id"]
    assert col.nullable is False


def test_external_sync_provider_not_nullable() -> None:
    """ExternalSync.provider must be NOT NULL."""
    col = inspect(ExternalSync).columns["provider"]
    assert col.nullable is False


def test_external_sync_provider_is_string_20() -> None:
    """ExternalSync.provider must be String(20)."""
    col = inspect(ExternalSync).columns["provider"]
    assert col.type.length == 20


def test_external_sync_last_synced_at_nullable() -> None:
    """ExternalSync.last_synced_at must be NULLABLE."""
    col = inspect(ExternalSync).columns["last_synced_at"]
    assert col.nullable is True


def test_external_sync_last_synced_at_is_datetime_tz() -> None:
    """ExternalSync.last_synced_at must be timezone-aware."""
    col = inspect(ExternalSync).columns["last_synced_at"]
    assert col.type.timezone is True


def test_external_sync_status_not_nullable() -> None:
    """ExternalSync.status must be NOT NULL."""
    col = inspect(ExternalSync).columns["status"]
    assert col.nullable is False


def test_external_sync_status_has_default_active() -> None:
    """ExternalSync.status must default to SyncStatus.ACTIVE."""
    col = inspect(ExternalSync).columns["status"]
    assert col.default is not None
    assert col.default.arg == SyncStatus.ACTIVE  # type: ignore[attr-defined]


def test_external_sync_sync_config_json_type() -> None:
    """ExternalSync.sync_config_json must be JSONB."""
    col = inspect(ExternalSync).columns["sync_config_json"]
    assert "JSONB" in str(col.type).upper()


def test_external_sync_sync_config_json_not_nullable() -> None:
    """ExternalSync.sync_config_json must be NOT NULL."""
    col = inspect(ExternalSync).columns["sync_config_json"]
    assert col.nullable is False


def test_external_sync_created_at_not_nullable() -> None:
    """ExternalSync.created_at must be NOT NULL."""
    col = inspect(ExternalSync).columns["created_at"]
    assert col.nullable is False


def test_external_sync_created_at_is_datetime_tz() -> None:
    """ExternalSync.created_at must be timezone-aware."""
    col = inspect(ExternalSync).columns["created_at"]
    assert col.type.timezone is True


def test_external_sync_has_provider_check_constraint() -> None:
    """ExternalSync must have a CHECK constraint on provider column."""
    constraints = {c.name for c in ExternalSync.__table__.constraints}  # type: ignore[attr-defined]
    assert "ck_external_syncs_provider" in constraints


def test_external_sync_has_status_check_constraint() -> None:
    """ExternalSync must have a CHECK constraint on status column."""
    constraints = {c.name for c in ExternalSync.__table__.constraints}  # type: ignore[attr-defined]
    assert "ck_external_syncs_status" in constraints


def test_external_sync_has_unique_user_provider_index() -> None:
    """ExternalSync must have a unique index on (user_id, provider)."""
    indexes = {idx.name: idx for idx in ExternalSync.__table__.indexes}  # type: ignore[attr-defined]
    assert "idx_external_sync_user_provider" in indexes
    assert indexes["idx_external_sync_user_provider"].unique is True


def test_sync_provider_enum_values() -> None:
    """SyncProvider enum must have google_calendar and github values."""
    assert SyncProvider.GOOGLE_CALENDAR.value == "google_calendar"
    assert SyncProvider.GITHUB.value == "github"


def test_sync_status_enum_values() -> None:
    """SyncStatus enum must have active, paused, and error values."""
    assert SyncStatus.ACTIVE.value == "active"
    assert SyncStatus.PAUSED.value == "paused"
    assert SyncStatus.ERROR.value == "error"


def test_external_sync_repr_contains_id() -> None:
    """ExternalSync.__repr__ should include the id for debugging."""
    sync_id = uuid.uuid4()
    obj = ExternalSync(
        id=sync_id,
        user_id=uuid.uuid4(),
        provider=SyncProvider.GITHUB,
    )
    assert str(sync_id) in repr(obj)
