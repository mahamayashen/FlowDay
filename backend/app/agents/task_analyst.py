"""Task Analyst agent — analyzes Task completion data for task management insights."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import TaskAnalystDeps, TaskAnalystResult
from app.core.config import settings

task_analyst: Agent[TaskAnalystDeps, TaskAnalystResult] = Agent(
    model=settings.LLM_MODEL,
    output_type=TaskAnalystResult,
    deps_type=TaskAnalystDeps,
    defer_model_check=True,
    system_prompt=(
        "You are a task management analyst. "
        "Given a list of tasks for a user, produce structured insights about their "
        "task completion patterns, priority breakdown, and overdue items. "
        "completion_rate_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0. "
        "overdue_tasks = tasks with due_date < analysis_date and status != 'done'. "
        "All numeric fields must be >= 0. completion_rate_pct must be between 0 and 100. "
        "Provide 2-4 concise, actionable insights in the insights list."
    ),
)


@task_analyst.instructions
async def add_task_context(ctx: RunContext[TaskAnalystDeps]) -> str:
    """Inject pre-fetched task data into the prompt."""
    deps = ctx.deps
    tasks = deps.tasks
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "done")
    completion_rate = (completed / total * 100) if total > 0 else 0.0

    overdue = sum(
        1
        for t in tasks
        if t.due_date is not None
        and t.due_date < deps.analysis_date
        and t.status != "done"
    )

    priority_dist: dict[str, int] = {}
    for t in tasks:
        priority_dist[t.priority] = priority_dist.get(t.priority, 0) + 1

    completion_times = [
        (t.completed_at - t.created_at).total_seconds() / 3600.0
        for t in tasks
        if t.completed_at is not None
    ]
    avg_completion = (
        sum(completion_times) / len(completion_times) if completion_times else None
    )

    return (
        f"Analysis date: {deps.analysis_date}\n"
        f"Total tasks: {total}\n"
        f"Completed tasks: {completed}\n"
        f"Completion rate: {completion_rate:.1f}%\n"
        f"Overdue tasks: {overdue}\n"
        f"Average completion time (hours): {avg_completion}\n"
        f"Priority distribution: {priority_dist}\n"
        f"Tasks: {[t.model_dump() for t in tasks]}"
    )
