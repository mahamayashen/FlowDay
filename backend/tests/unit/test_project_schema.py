from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

# ---------------------------------------------------------------------------
# ProjectCreate
# ---------------------------------------------------------------------------


def test_create_requires_name_and_color() -> None:
    """ProjectCreate must require name and color."""
    p = ProjectCreate(name="Work", color="#FF0000")
    assert p.name == "Work"
    assert p.color == "#FF0000"


def test_create_optional_fields_default_to_none() -> None:
    """client_name and hourly_rate must default to None."""
    p = ProjectCreate(name="Work", color="#FF0000")
    assert p.client_name is None
    assert p.hourly_rate is None


def test_create_with_all_fields() -> None:
    """ProjectCreate must accept all optional fields."""
    p = ProjectCreate(
        name="Work",
        color="#00FF00",
        client_name="Acme Corp",
        hourly_rate=Decimal("150.00"),
    )
    assert p.client_name == "Acme Corp"
    assert p.hourly_rate == Decimal("150.00")


def test_create_rejects_missing_name() -> None:
    """ProjectCreate without name must raise ValidationError."""
    with pytest.raises(ValidationError):
        ProjectCreate(color="#FF0000")  # type: ignore[call-arg]


def test_create_rejects_missing_color() -> None:
    """ProjectCreate without color must raise ValidationError."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="Work")  # type: ignore[call-arg]


def test_create_rejects_invalid_hex_color() -> None:
    """ProjectCreate must reject non-hex color strings."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="Work", color="red")


def test_create_accepts_valid_hex_colors() -> None:
    """ProjectCreate must accept 4-char and 7-char hex colors."""
    p3 = ProjectCreate(name="A", color="#FFF")
    assert p3.color == "#FFF"
    p6 = ProjectCreate(name="B", color="#FF00FF")
    assert p6.color == "#FF00FF"


# ---------------------------------------------------------------------------
# ProjectUpdate
# ---------------------------------------------------------------------------


def test_update_all_fields_optional() -> None:
    """ProjectUpdate must allow empty (no fields set)."""
    p = ProjectUpdate()
    assert p.name is None
    assert p.color is None
    assert p.client_name is None
    assert p.hourly_rate is None
    assert p.status is None


def test_update_partial_fields() -> None:
    """ProjectUpdate must accept partial updates."""
    p = ProjectUpdate(name="New Name")
    assert p.name == "New Name"
    assert p.color is None


def test_update_rejects_invalid_hex_color() -> None:
    """ProjectUpdate must reject non-hex color if provided."""
    with pytest.raises(ValidationError):
        ProjectUpdate(color="not-hex")


# ---------------------------------------------------------------------------
# ProjectResponse
# ---------------------------------------------------------------------------


def test_response_from_attributes() -> None:
    """ProjectResponse must support from_attributes (ORM mode)."""
    assert ProjectResponse.model_config.get("from_attributes") is True


def test_response_round_trip() -> None:
    """ProjectResponse must serialize all project fields."""
    now = datetime.now(UTC)
    uid = uuid.uuid4()
    pid = uuid.uuid4()
    resp = ProjectResponse(
        id=pid,
        user_id=uid,
        name="Test",
        color="#ABCDEF",
        client_name="Client",
        hourly_rate=Decimal("99.50"),
        status="active",
        created_at=now,
    )
    assert resp.id == pid
    assert resp.user_id == uid
    assert resp.status == "active"
    assert resp.hourly_rate == Decimal("99.50")
