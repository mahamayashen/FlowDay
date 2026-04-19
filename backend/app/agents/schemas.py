"""Pydantic schemas for agent deps and result types (Group A parallel analysts)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

from pydantic import BaseModel, Field

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


# ---------------------------------------------------------------------------
# Code Analyst
# ---------------------------------------------------------------------------


class GitHubSyncData(BaseModel):
    """GitHub sync metadata — populated when a GitHub sync record exists."""

    last_synced_at: datetime | None
    sync_config: dict[str, object]


@dataclass
class CodeAnalystDeps:
    """Dependencies injected into the Code Analyst via RunContext."""

    user_id: uuid.UUID
    analysis_date: date
    github_sync: GitHubSyncData | None = None


class CodeAnalystResult(BaseModel):
    """Structured output produced by the Code Analyst agent."""

    data_available: bool
    commits_count: int
    pull_requests_count: int
    avg_pr_cycle_hours: float | None
    most_active_repo: str | None
    insights: list[str]


# ---------------------------------------------------------------------------
# Task Analyst
# ---------------------------------------------------------------------------


class TaskData(BaseModel):
    """A single task pre-fetched for the Task Analyst."""

    task_id: uuid.UUID
    title: str
    project_name: str
    status: str  # "todo" | "in_progress" | "done"
    priority: str  # "low" | "medium" | "high" | "urgent"
    estimate_minutes: int | None
    due_date: date | None
    created_at: datetime
    completed_at: datetime | None


@dataclass
class TaskAnalystDeps:
    """Dependencies injected into the Task Analyst via RunContext."""

    user_id: uuid.UUID
    analysis_date: date
    tasks: list[TaskData] = field(default_factory=list)


class TaskAnalystResult(BaseModel):
    """Structured output produced by the Task Analyst agent."""

    total_tasks: int
    completed_tasks: int
    completion_rate_pct: float
    overdue_tasks: int
    avg_completion_hours: float | None
    priority_distribution: dict[str, int]
    insights: list[str]


# ---------------------------------------------------------------------------
# Group A aggregate result
# ---------------------------------------------------------------------------


class GroupAResult(BaseModel):
    """Aggregated output from all four Group A parallel analyst agents."""

    time_analysis: TimeAnalystResult | None = None
    meeting_analysis: MeetingAnalystResult | None = None
    code_analysis: CodeAnalystResult | None = None
    task_analysis: TaskAnalystResult | None = None
    errors: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pattern Detector (Group B)
# ---------------------------------------------------------------------------


class CrossPattern(BaseModel):
    """A single cross-source correlation pattern detected by the Pattern Detector."""

    category: str  # e.g. "time-meeting", "code-task", "time-task", "meeting-task"
    pattern: str  # human-readable description of the correlation
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]  # specific data points from Group A supporting this pattern
    recommendation: str  # actionable suggestion


@dataclass
class PatternDetectorDeps:
    """Dependencies injected into the Pattern Detector via RunContext."""

    user_id: uuid.UUID
    analysis_date: date
    group_a_result: GroupAResult


class PatternDetectorResult(BaseModel):
    """Structured output produced by the Pattern Detector agent."""

    patterns: list[CrossPattern]
    summary: str
