"""Shared fixtures for agent unit tests."""

from __future__ import annotations

import pytest

from app.agents.schemas import (
    CodeAnalystResult,
    CrossPattern,
    GroupAResult,
    MeetingAnalystResult,
    PatternDetectorResult,
    TaskAnalystResult,
    TimeAnalystResult,
)


@pytest.fixture
def full_group_a_result() -> GroupAResult:
    return GroupAResult(
        time_analysis=TimeAnalystResult(
            total_tracked_hours=6.5,
            total_planned_hours=8.0,
            utilization_pct=81.25,
            most_active_project="FlowDay",
            avg_session_minutes=97.5,
            insights=["Good focus time", "Utilization above 80%"],
        ),
        meeting_analysis=MeetingAnalystResult(
            total_meeting_hours=2.5,
            meeting_count=3,
            avg_meeting_duration_hours=0.83,
            longest_meeting_hours=1.0,
            focus_time_hours=5.5,
            insights=["Moderate meeting load"],
        ),
        code_analysis=CodeAnalystResult(
            data_available=True,
            commits_count=5,
            pull_requests_count=2,
            avg_pr_cycle_hours=4.0,
            most_active_repo="flowday-main",
            insights=["Steady commit pace"],
        ),
        task_analysis=TaskAnalystResult(
            total_tasks=12,
            completed_tasks=4,
            completion_rate_pct=33.3,
            overdue_tasks=2,
            avg_completion_hours=3.5,
            priority_distribution={"high": 3, "medium": 5, "low": 4},
            insights=["2 overdue tasks need attention"],
        ),
        errors={},
    )


@pytest.fixture
def partial_group_a_result() -> GroupAResult:
    """Group A result with time and code analysis missing (simulating failures)."""
    return GroupAResult(
        time_analysis=None,
        meeting_analysis=MeetingAnalystResult(
            total_meeting_hours=3.0,
            meeting_count=4,
            avg_meeting_duration_hours=0.75,
            longest_meeting_hours=1.5,
            focus_time_hours=5.0,
            insights=["Heavy meeting day"],
        ),
        code_analysis=None,
        task_analysis=TaskAnalystResult(
            total_tasks=8,
            completed_tasks=2,
            completion_rate_pct=25.0,
            overdue_tasks=3,
            avg_completion_hours=None,
            priority_distribution={"high": 4, "medium": 3, "low": 1},
            insights=["Low completion rate", "3 overdue tasks"],
        ),
        errors={"time_analyst": "timeout", "code_analyst": "no github"},
    )


@pytest.fixture
def sample_pattern_result() -> PatternDetectorResult:
    return PatternDetectorResult(
        patterns=[
            CrossPattern(
                category="time-meeting",
                pattern="High meeting load correlates with low tracked hours",
                confidence=0.85,
                evidence=["2.5h meetings", "6.5h tracked vs 8h planned"],
                recommendation="Block focus time before afternoon meetings",
            ),
            CrossPattern(
                category="code-task",
                pattern="Commit activity aligns with high-priority task completion",
                confidence=0.72,
                evidence=["5 commits", "4 tasks completed"],
                recommendation="Maintain current sprint rhythm",
            ),
        ],
        summary="Two cross-source patterns detected with moderate-to-high confidence.",
    )
