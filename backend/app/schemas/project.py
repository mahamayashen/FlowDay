from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectStatus

_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_VALID_STATUSES = {s.value for s in ProjectStatus}


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(min_length=1, max_length=100)
    color: str
    client_name: str | None = Field(default=None, max_length=100)
    hourly_rate: Decimal | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        """Name must not be blank after stripping whitespace."""
        v = v.strip()
        if not v:
            msg = "name must not be blank"
            raise ValueError(msg)
        return v

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Color must be a valid hex color code (#RGB or #RRGGBB).

        Normalizes 3-char hex (#FFF) to 6-char (#FFFFFF) for consistency
        with the String(7) DB column.
        """
        if not _HEX_COLOR_RE.match(v):
            msg = "color must be a hex color code (e.g. #FF0000 or #FFF)"
            raise ValueError(msg)
        if len(v) == 4:
            v = "#" + "".join(c * 2 for c in v[1:])
        return v


class ProjectUpdate(BaseModel):
    """Schema for partially updating a project."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None
    client_name: str | None = Field(default=None, max_length=100)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    status: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str | None) -> str | None:
        """Name must not be blank after stripping whitespace if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                msg = "name must not be blank"
                raise ValueError(msg)
        return v

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        """Color must be a valid hex color code if provided.

        Normalizes 3-char hex (#FFF) to 6-char (#FFFFFF).
        """
        if v is not None and not _HEX_COLOR_RE.match(v):
            msg = "color must be a hex color code (e.g. #FF0000 or #FFF)"
            raise ValueError(msg)
        if v is not None and len(v) == 4:
            v = "#" + "".join(c * 2 for c in v[1:])
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Status must be a valid ProjectStatus value if provided."""
        if v is not None and v not in _VALID_STATUSES:
            msg = f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}"
            raise ValueError(msg)
        return v


class ProjectResponse(BaseModel):
    """Public project representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: str
    client_name: str | None
    hourly_rate: Decimal | None
    status: str
    created_at: datetime
