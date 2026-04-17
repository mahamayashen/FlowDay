from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncStatusResponse(BaseModel):
    """Response schema for an ExternalSync record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    status: str
    last_synced_at: datetime | None
    sync_config_json: dict  # type: ignore[type-arg]
    created_at: datetime
