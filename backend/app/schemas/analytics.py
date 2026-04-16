from __future__ import annotations

import enum
import uuid
from datetime import date

from pydantic import BaseModel


class StatusTag(enum.StrEnum):
    """Planned-vs-actual comparison status for a task."""

    DONE = "done"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    UNPLANNED = "unplanned"


class TaskComparison(BaseModel):
    """Single task planned-vs-actual comparison."""

    task_id: uuid.UUID
    task_title: str
    planned_hours: float
    actual_hours: float
    status: StatusTag


class PlannedVsActualSummary(BaseModel):
    """Aggregate totals for the day."""

    total_planned_hours: float
    total_actual_hours: float
    done_count: int
    partial_count: int
    skipped_count: int
    unplanned_count: int


class PlannedVsActualResponse(BaseModel):
    """Full response for the planned-vs-actual endpoint."""

    date: date
    tasks: list[TaskComparison]
    summary: PlannedVsActualSummary
