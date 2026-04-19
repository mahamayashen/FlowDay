"""Pattern Detector agent — finds cross-source correlations in Group A outputs."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import PatternDetectorDeps, PatternDetectorResult
from app.core.config import settings

pattern_detector: Agent[PatternDetectorDeps, PatternDetectorResult] = Agent(
    model=settings.LLM_MODEL,
    output_type=PatternDetectorResult,
    deps_type=PatternDetectorDeps,
    defer_model_check=True,
    system_prompt=(
        "You are a cross-source pattern detector. "
        "Given structured outputs from four analyst agents (time, meeting, code, task), "
        "identify correlations and patterns across data sources. "
        "Each pattern must have a category indicating which sources it correlates "
        "(e.g. 'time-meeting', 'code-task', 'time-task', 'meeting-task'). "
        "Confidence scores must be between 0.0 and 1.0. "
        "Evidence must reference specific data points from the analyst outputs. "
        "Provide 2-5 patterns with actionable recommendations. "
        "If some analyst outputs are missing, only detect patterns from available data."
    ),
)


@pattern_detector.instructions
async def add_group_a_context(ctx: RunContext[PatternDetectorDeps]) -> str:
    """Serialize Group A results into the prompt for cross-correlation analysis."""
    deps = ctx.deps
    ga = deps.group_a_result
    sections = [f"Analysis date: {deps.analysis_date}"]

    if ga.time_analysis:
        t = ga.time_analysis
        sections.append(
            f"TIME ANALYSIS:\n"
            f"  Tracked hours: {t.total_tracked_hours:.2f}\n"
            f"  Planned hours: {t.total_planned_hours:.2f}\n"
            f"  Utilization: {t.utilization_pct:.1f}%\n"
            f"  Most active project: {t.most_active_project or 'none'}\n"
            f"  Avg session: {t.avg_session_minutes:.1f} min\n"
            f"  Insights: {t.insights}"
        )
    else:
        sections.append("TIME ANALYSIS: unavailable")

    if ga.meeting_analysis:
        m = ga.meeting_analysis
        sections.append(
            f"MEETING ANALYSIS:\n"
            f"  Meeting hours: {m.total_meeting_hours:.2f}\n"
            f"  Meeting count: {m.meeting_count}\n"
            f"  Avg duration: {m.avg_meeting_duration_hours:.2f}h\n"
            f"  Focus time: {m.focus_time_hours:.2f}h\n"
            f"  Insights: {m.insights}"
        )
    else:
        sections.append("MEETING ANALYSIS: unavailable")

    if ga.code_analysis:
        c = ga.code_analysis
        sections.append(
            f"CODE ANALYSIS:\n"
            f"  Data available: {c.data_available}\n"
            f"  Commits: {c.commits_count}\n"
            f"  PRs: {c.pull_requests_count}\n"
            f"  Avg PR cycle: {c.avg_pr_cycle_hours}h\n"
            f"  Most active repo: {c.most_active_repo or 'none'}\n"
            f"  Insights: {c.insights}"
        )
    else:
        sections.append("CODE ANALYSIS: unavailable")

    if ga.task_analysis:
        tk = ga.task_analysis
        sections.append(
            f"TASK ANALYSIS:\n"
            f"  Total tasks: {tk.total_tasks}\n"
            f"  Completed: {tk.completed_tasks}\n"
            f"  Completion rate: {tk.completion_rate_pct:.1f}%\n"
            f"  Overdue: {tk.overdue_tasks}\n"
            f"  Avg completion time: {tk.avg_completion_hours}h\n"
            f"  Priority distribution: {tk.priority_distribution}\n"
            f"  Insights: {tk.insights}"
        )
    else:
        sections.append("TASK ANALYSIS: unavailable")

    if ga.errors:
        sections.append(f"ERRORS: {ga.errors}")

    return "\n\n".join(sections)
