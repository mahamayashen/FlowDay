from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimeEntryStart(BaseModel):
    """Schema for starting a new timer."""

    task_id: uuid.UUID
    started_at: datetime | None = None


class TimeEntryResponse(BaseModel):
    """Public time entry representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    created_at: datetime
