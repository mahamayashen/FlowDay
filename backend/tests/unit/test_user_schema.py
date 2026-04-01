from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.user import TokenResponse, UserCreate, UserResponse


def test_user_response_excludes_oauth_tokens() -> None:
    """UserResponse must not expose google_oauth_token or github_oauth_token."""
    fields = set(UserResponse.model_fields.keys())
    assert "google_oauth_token" not in fields
    assert "github_oauth_token" not in fields
    assert "hashed_password" not in fields


def test_user_response_includes_id_email_name() -> None:
    """UserResponse must include id, email, and name."""
    fields = set(UserResponse.model_fields.keys())
    assert {"id", "email", "name"}.issubset(fields)


def test_user_response_from_orm() -> None:
    """UserResponse can be constructed from an ORM-like object via model_validate."""

    class FakeUser:
        def __init__(self) -> None:
            self.id = uuid.uuid4()
            self.email = "test@example.com"
            self.name = "Test User"
            self.settings_json = {}
            self.created_at = datetime.now(UTC)

    response = UserResponse.model_validate(FakeUser(), from_attributes=True)
    assert response.email == "test@example.com"
    assert response.name == "Test User"


def test_user_create_schema_validates_email() -> None:
    """UserCreate with an invalid email must raise ValidationError."""
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", name="Test")


def test_user_create_accepts_valid_email() -> None:
    """UserCreate with a valid email must succeed."""
    user = UserCreate(email="valid@example.com", name="Test")
    assert user.email == "valid@example.com"


def test_token_response_has_required_fields() -> None:
    """TokenResponse must have access_token, refresh_token, token_type."""
    token = TokenResponse(access_token="abc", refresh_token="def", token_type="bearer")
    assert token.access_token == "abc"
    assert token.token_type == "bearer"
