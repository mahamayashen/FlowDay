"""Pydantic schemas for WeeklyReview API responses."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class WeeklyReviewResponse(BaseModel):
    """API response schema for a WeeklyReview."""

    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    status: str
    narrative: str | None
    insights_json: dict[str, Any] | None
    scores_json: dict[str, Any] | None
    agent_metadata_json: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
