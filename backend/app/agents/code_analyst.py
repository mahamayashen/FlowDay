"""Code Analyst agent — analyzes GitHub sync data for code productivity insights."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import CodeAnalystDeps, CodeAnalystResult
from app.core.config import settings

code_analyst: Agent[CodeAnalystDeps, CodeAnalystResult] = Agent(
    model=settings.LLM_MODEL,
    output_type=CodeAnalystResult,
    deps_type=CodeAnalystDeps,
    defer_model_check=True,
    system_prompt=(
        "You are a code productivity analyst. "
        "Given GitHub sync metadata for a user, produce structured insights about "
        "their code productivity. "
        "When data_available is false (no GitHub sync configured), set all numeric "
        "fields to 0, set data_available=false, avg_pr_cycle_hours and most_active_repo "
        "to null, and provide a single insight explaining that GitHub is not connected. "
        "Provide 2-4 concise, actionable insights otherwise."
    ),
)


@code_analyst.instructions
async def add_code_context(ctx: RunContext[CodeAnalystDeps]) -> str:
    """Inject pre-fetched GitHub sync data into the prompt."""
    deps = ctx.deps
    if deps.github_sync is None:
        return (
            f"Analysis date: {deps.analysis_date}\n"
            "GitHub sync: NOT CONFIGURED\n"
            "data_available must be false. Return zeroed metrics."
        )
    sync = deps.github_sync
    return (
        f"Analysis date: {deps.analysis_date}\n"
        f"Last synced at: {sync.last_synced_at}\n"
        f"Sync configuration: {sync.sync_config}\n"
        "data_available must be true."
    )
