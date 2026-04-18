"""Meeting Analyst agent — analyzes Google Calendar data for meeting load insights."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import MeetingAnalystDeps, MeetingAnalystResult
from app.core.config import settings

_WORKDAY_HOURS = 8.0

meeting_analyst: Agent[MeetingAnalystDeps, MeetingAnalystResult] = Agent(
    model=settings.LLM_MODEL,
    output_type=MeetingAnalystResult,
    deps_type=MeetingAnalystDeps,
    defer_model_check=True,
    system_prompt=(
        "You are a meeting load analyst. "
        "Given a list of calendar events for a user's day, produce structured insights "
        "about their meeting burden and available focus time. "
        "All numeric fields must be >= 0. focus_time_hours = max(0, 8 - total_meeting_hours). "
        "Provide 2-4 concise, actionable insights in the insights list."
    ),
)


@meeting_analyst.instructions
async def add_meeting_context(ctx: RunContext[MeetingAnalystDeps]) -> str:
    """Inject pre-fetched calendar block data into the prompt."""
    deps = ctx.deps
    blocks = deps.calendar_blocks
    meeting_count = len(blocks)
    durations = [b.end_hour - b.start_hour for b in blocks]
    total_hours = sum(durations)
    avg_hours = total_hours / meeting_count if meeting_count > 0 else 0.0
    longest_hours = max(durations) if durations else 0.0
    focus_hours = max(0.0, _WORKDAY_HOURS - total_hours)

    return (
        f"Analysis date: {deps.analysis_date}\n"
        f"Number of meetings: {meeting_count}\n"
        f"Total meeting hours: {total_hours:.2f}\n"
        f"Average meeting duration (hours): {avg_hours:.2f}\n"
        f"Longest meeting (hours): {longest_hours:.2f}\n"
        f"Focus time available (hours): {focus_hours:.2f}\n"
        f"Meetings: {[b.model_dump() for b in blocks]}"
    )
