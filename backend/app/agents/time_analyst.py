"""Time Analyst agent — analyzes TimeEntry data for time utilization insights."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import TimeAnalystDeps, TimeAnalystResult
from app.core.config import settings

time_analyst: Agent[TimeAnalystDeps, TimeAnalystResult] = Agent(
    model=settings.LLM_MODEL,
    output_type=TimeAnalystResult,
    deps_type=TimeAnalystDeps,
    defer_model_check=True,
    system_prompt=(
        "You are a time utilization analyst. "
        "Given time tracking data for a user's work day, produce structured insights "
        "about how their time was spent. "
        "All numeric fields must be >= 0. "
        "Provide 2-4 concise, actionable insights in the insights list."
    ),
)


@time_analyst.instructions
async def add_time_context(ctx: RunContext[TimeAnalystDeps]) -> str:
    """Inject pre-fetched time entry data into the prompt."""
    deps = ctx.deps
    total_tracked = sum(e.duration_seconds for e in deps.time_entries) / 3600.0
    total_planned = sum(
        b.end_hour - b.start_hour
        for b in deps.schedule_blocks
        if b.source == "manual"
    )
    sessions = len(deps.time_entries)
    avg_session = (
        (total_tracked * 60 / sessions) if sessions > 0 else 0.0
    )

    projects: dict[str, float] = {}
    for entry in deps.time_entries:
        projects[entry.project_name] = (
            projects.get(entry.project_name, 0.0) + entry.duration_seconds / 3600.0
        )
    most_active = max(projects, key=lambda k: projects[k]) if projects else None

    return (
        f"Analysis date: {deps.analysis_date}\n"
        f"Total tracked hours: {total_tracked:.2f}\n"
        f"Total planned hours: {total_planned:.2f}\n"
        f"Number of sessions: {sessions}\n"
        f"Average session length (minutes): {avg_session:.1f}\n"
        f"Most active project: {most_active or 'none'}\n"
        f"Time entries: {[e.model_dump() for e in deps.time_entries]}\n"
        f"Schedule blocks: {[b.model_dump() for b in deps.schedule_blocks]}"
    )
