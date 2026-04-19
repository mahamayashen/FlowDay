"""Narrative Writer agent — produces descriptive weekly review from Group A + B outputs."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import NarrativeWriterDeps, NarrativeWriterResult
from app.core.config import settings

narrative_writer: Agent[NarrativeWriterDeps, NarrativeWriterResult] = Agent(
    model=settings.LLM_MODEL,
    output_type=NarrativeWriterResult,
    deps_type=NarrativeWriterDeps,
    defer_model_check=True,
    system_prompt=(
        "You are a narrative writer for weekly productivity reviews. "
        "Given structured outputs from analyst agents and cross-source patterns, "
        "produce a descriptive and diagnostic narrative with exactly four sections: "
        "1) executive_summary: a high-level overview of the week's productivity, "
        "2) time_analysis: how time was allocated and utilised across projects and meetings, "
        "3) productivity_patterns: recurring themes and cross-source correlations observed, "
        "4) areas_of_concern: issues or risks identified in the data. "
        "Be DESCRIPTIVE and DIAGNOSTIC only — describe what happened and why. "
        "Do NOT provide prescriptive recommendations or action items. "
        "If some data sources are unavailable, note their absence and work with available data."
    ),
)


@narrative_writer.instructions
async def add_analysis_context(ctx: RunContext[NarrativeWriterDeps]) -> str:
    """Serialize Group A and Pattern Detector results into the prompt."""
    deps = ctx.deps
    ga = deps.group_a_result
    pd = deps.pattern_result
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

    if pd.patterns:
        pattern_lines = []
        for p in pd.patterns:
            pattern_lines.append(
                f"  - [{p.category}] {p.pattern} "
                f"(confidence: {p.confidence:.2f})\n"
                f"    Evidence: {p.evidence}"
            )
        sections.append("DETECTED PATTERNS:\n" + "\n".join(pattern_lines))
    else:
        sections.append("DETECTED PATTERNS: none")

    sections.append(f"PATTERN SUMMARY: {pd.summary}")

    return "\n\n".join(sections)
