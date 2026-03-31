from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.models.user import User


def test_user_model_has_required_columns() -> None:
    """User model must have all columns defined in DATA_MODEL.md."""
    columns = {c.name for c in inspect(User).columns}
    expected = {
        "id",
        "email",
        "name",
        "hashed_password",
        "google_oauth_token",
        "github_oauth_token",
        "settings_json",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_user_id_is_uuid() -> None:
    """User.id column type must be UUID."""
    col = inspect(User).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_user_email_is_unique() -> None:
    """User.email must have a unique constraint."""
    col = inspect(User).columns["email"]
    assert col.unique is True


def test_user_settings_json_defaults_to_empty() -> None:
    """User.settings_json must have a server default of '{}'."""
    col = inspect(User).columns["settings_json"]
    assert col.server_default is not None
    assert "'{}'" in str(col.server_default.arg) or "{}" in str(col.server_default.arg)


def test_user_table_name_is_users() -> None:
    """User.__tablename__ must be 'users'."""
    assert User.__tablename__ == "users"


def test_user_repr_contains_email() -> None:
    """User.__repr__ should include the email for debugging."""
    u = User(id=uuid.uuid4(), email="test@example.com", name="Test")
    assert "test@example.com" in repr(u)
