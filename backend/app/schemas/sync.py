from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SyncStatusResponse(BaseModel):
    """Response schema for an ExternalSync record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    status: str
    last_synced_at: datetime | None
    sync_config_json: dict[str, Any]
    created_at: datetime
