"""Pydantic schemas for agent deps and result types (Group A parallel analysts)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared data transfer objects (pre-fetched from DB before agent calls)
# ---------------------------------------------------------------------------


class TimeEntryData(BaseModel):
    """A single time entry pre-fetched for the Time Analyst."""

    task_id: uuid.UUID
    task_title: str
    project_name: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int


class ScheduleBlockData(BaseModel):
    """A schedule block pre-fetched for Time / Meeting analysts."""

    task_id: uuid.UUID
    task_title: str
    date: date
    start_hour: float
    end_hour: float
    source: str  # "manual" | "google_calendar"


# ---------------------------------------------------------------------------
# Time Analyst
# ---------------------------------------------------------------------------


@dataclass
class TimeAnalystDeps:
    """Dependencies injected into the Time Analyst via RunContext."""

    user_id: uuid.UUID
    analysis_date: date
    time_entries: list[TimeEntryData] = field(default_factory=list)
    schedule_blocks: list[ScheduleBlockData] = field(default_factory=list)


class TimeAnalystResult(BaseModel):
    """Structured output produced by the Time Analyst agent."""

    total_tracked_hours: float
    total_planned_hours: float
    utilization_pct: float
    most_active_project: str | None
    avg_session_minutes: float
    insights: list[str]


# ---------------------------------------------------------------------------
# Meeting Analyst
# ---------------------------------------------------------------------------


@dataclass
class MeetingAnalystDeps:
    """Dependencies injected into the Meeting Analyst via RunContext."""

    user_id: uuid.UUID
    analysis_date: date
    calendar_blocks: list[ScheduleBlockData] = field(default_factory=list)


class MeetingAnalystResult(BaseModel):
    """Structured output produced by the Meeting Analyst agent."""

    total_meeting_hours: float
    meeting_count: int
    avg_meeting_duration_hours: float
    longest_meeting_hours: float
    focus_time_hours: float
    insights: list[str]
