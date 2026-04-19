"""Judge agent — LLM-as-Judge scoring of weekly review narratives (Group D).

Uses a different LLM provider than the Narrative Writer to avoid self-bias.
"""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas import JudgeDeps, JudgeResult
from app.core.config import settings

judge: Agent[JudgeDeps, JudgeResult] = Agent(
    model=settings.LLM_JUDGE_MODEL,
    output_type=JudgeResult,
    deps_type=JudgeDeps,
    defer_model_check=True,
    system_prompt=(
        "You are an impartial evaluator of weekly productivity review narratives. "
        "Given a narrative produced by an AI writer and the underlying data it was based on, "
        "score the narrative on three dimensions (each from 1 to 10): "
        "1) actionability_score: Are the observations specific and grounded enough to act on? "
        "2) accuracy_score: Does the narrative accurately reflect the underlying data? "
        "3) coherence_score: Is the narrative internally consistent and logically structured? "
        "Then provide an overall_score (1–10) as a holistic assessment. "
        "Finally, provide a brief feedback string explaining the scores. "
        "Be critical but fair. Base scores solely on the data and narrative provided."
    ),
)


@judge.instructions
async def add_evaluation_context(ctx: RunContext[JudgeDeps]) -> str:
    """Serialize the narrative and underlying pipeline data into the prompt."""
    deps = ctx.deps
    nw = deps.narrative_result
    ga = deps.group_a_result
    pd = deps.pattern_result

    sections = [
        f"Analysis date: {deps.analysis_date}",
        "--- NARRATIVE TO EVALUATE ---",
        f"Executive Summary:\n{nw.executive_summary}",
        f"Time Analysis:\n{nw.time_analysis}",
        f"Productivity Patterns:\n{nw.productivity_patterns}",
        f"Areas of Concern:\n{nw.areas_of_concern}",
        "--- UNDERLYING DATA ---",
    ]

    if ga.time_analysis:
        t = ga.time_analysis
        sections.append(
            f"TIME: tracked={t.total_tracked_hours:.2f}h, "
            f"planned={t.total_planned_hours:.2f}h, "
            f"utilization={t.utilization_pct:.1f}%"
        )
    else:
        sections.append("TIME: unavailable")

    if ga.meeting_analysis:
        m = ga.meeting_analysis
        sections.append(
            f"MEETINGS: {m.meeting_count} meetings, "
            f"{m.total_meeting_hours:.2f}h total, "
            f"focus={m.focus_time_hours:.2f}h"
        )
    else:
        sections.append("MEETINGS: unavailable")

    if ga.code_analysis:
        c = ga.code_analysis
        sections.append(
            f"CODE: commits={c.commits_count}, prs={c.pull_requests_count}"
        )
    else:
        sections.append("CODE: unavailable")

    if ga.task_analysis:
        tk = ga.task_analysis
        sections.append(
            f"TASKS: {tk.completed_tasks}/{tk.total_tasks} completed "
            f"({tk.completion_rate_pct:.1f}%), overdue={tk.overdue_tasks}"
        )
    else:
        sections.append("TASKS: unavailable")

    if pd.patterns:
        pattern_lines = [
            f"  - [{p.category}] {p.pattern} (confidence={p.confidence:.2f})"
            for p in pd.patterns
        ]
        sections.append("PATTERNS:\n" + "\n".join(pattern_lines))
    else:
        sections.append("PATTERNS: none detected")

    return "\n\n".join(sections)
