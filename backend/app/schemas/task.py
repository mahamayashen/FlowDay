from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority, TaskStatus

_VALID_PRIORITIES = {s.value for s in TaskPriority}
_VALID_STATUSES = {s.value for s in TaskStatus}


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    estimate_minutes: int | None = Field(default=None, ge=0)
    priority: str = "medium"
    status: str = "todo"
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        """Title must not be blank after stripping whitespace."""
        v = v.strip()
        if not v:
            msg = "title must not be blank"
            raise ValueError(msg)
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Priority must be a valid TaskPriority value."""
        if v not in _VALID_PRIORITIES:
            msg = f"priority must be one of: {', '.join(sorted(_VALID_PRIORITIES))}"
            raise ValueError(msg)
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Status must be a valid TaskStatus value."""
        if v not in _VALID_STATUSES:
            msg = f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}"
            raise ValueError(msg)
        return v


class TaskUpdate(BaseModel):
    """Schema for partially updating a task."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    estimate_minutes: int | None = Field(default=None, ge=0)
    priority: str | None = None
    status: str | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str | None) -> str | None:
        """Title must not be blank after stripping whitespace if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                msg = "title must not be blank"
                raise ValueError(msg)
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        """Priority must be a valid TaskPriority value if provided."""
        if v is not None and v not in _VALID_PRIORITIES:
            msg = f"priority must be one of: {', '.join(sorted(_VALID_PRIORITIES))}"
            raise ValueError(msg)
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Status must be a valid TaskStatus value if provided."""
        if v is not None and v not in _VALID_STATUSES:
            msg = f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}"
            raise ValueError(msg)
        return v


class TaskResponse(BaseModel):
    """Public task representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    estimate_minutes: int | None
    priority: str
    status: str
    due_date: date | None
    created_at: datetime
    completed_at: datetime | None
