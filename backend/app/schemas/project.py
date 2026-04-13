from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.project import ProjectStatus

_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_VALID_STATUSES = {s.value for s in ProjectStatus}


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str
    color: str
    client_name: str | None = None
    hourly_rate: Decimal | None = None

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Color must be a valid hex color code (#RGB or #RRGGBB)."""
        if not _HEX_COLOR_RE.match(v):
            msg = "color must be a hex color code (e.g. #FF0000 or #FFF)"
            raise ValueError(msg)
        return v


class ProjectUpdate(BaseModel):
    """Schema for partially updating a project."""

    name: str | None = None
    color: str | None = None
    client_name: str | None = None
    hourly_rate: Decimal | None = None
    status: str | None = None

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        """Color must be a valid hex color code if provided."""
        if v is not None and not _HEX_COLOR_RE.match(v):
            msg = "color must be a hex color code (e.g. #FF0000 or #FFF)"
            raise ValueError(msg)
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
