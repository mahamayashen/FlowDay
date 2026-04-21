# Building FlowDay: What I Learned Orchestrating AI Agents with Claude Code

*How a parallel multi-agent pipeline, LLM-as-Judge evaluation, and AI-assisted TDD came together in a production-grade daily planner.*

---

FlowDay started with a simple observation: freelancers juggling multiple clients live in two disconnected worlds. Their calendar tells them *when* they're busy. Their task manager tells them *what* to do. Neither tells them *how well* they're actually spending their time. FlowDay connects those dots — and the most interesting part of building it wasn't the planner UI, but the AI system that reviews your work week.

This post covers the technical decisions, AI architecture, and development workflow behind FlowDay — and what surprised me about using Claude Code as a core part of the engineering process.

## The AI Pipeline: Why Parallel Agents?

The heart of FlowDay is a weekly review system. Every week, it pulls together your time entries, calendar events, GitHub commits, and task completions, then generates a narrative analysis of your productivity patterns. A single LLM call could do this, but the output quality would be inconsistent and hard to debug.

Instead, I built a four-group pipeline using Pydantic AI:

**Group A** runs four specialist agents in parallel via `asyncio.gather` — a Time Analyst, Meeting Analyst, Code Analyst, and Task Analyst. Each agent has a narrow focus and a Pydantic `result_type` schema that constrains its output. Running them concurrently cuts latency to the time of the slowest agent rather than the sum of all four.

**Group B** is a Pattern Detector that receives all Group A outputs and finds cross-source correlations. For instance: "Weeks with more than 6 hours of meetings correlate with lower task completion rates" — something no single analyst could surface.

**Group C** is the Narrative Writer, which synthesizes everything into a human-readable weekly summary.

**Group D** is the Judge — and this is where the architecture gets interesting.

## LLM-as-Judge: Grading Your Own Homework (With a Different Pencil)

The Judge agent scores each narrative on three dimensions: actionability, accuracy, and coherence. Crucially, it runs on a *different LLM provider* than the Narrative Writer. This avoids the well-documented self-preference bias where models rate their own outputs higher than they deserve.

If the score falls below a threshold, the Judge triggers a `ModelRetry` — Pydantic AI's built-in retry mechanism — sending the narrative back for regeneration with specific feedback. This can happen up to twice before accepting the best attempt.

This pattern — automated quality evaluation with cross-provider scoring — turned out to be more practical than I expected. It catches issues like vague recommendations ("try to be more productive"), hallucinated statistics, and narratives that bury the key insight in paragraph four.

## The Claude Code Workflow: AI-Assisted TDD at Scale

The development workflow was where Claude Code made the biggest difference. We defined a strict 4-phase process for every GitHub issue:

1. **Explore** — Claude reads the codebase and maps the blast radius of a change. No files are modified. This phase alone saved us from multiple wrong-direction starts.

2. **Plan** — Claude writes an implementation plan with acceptance criteria, mapped to TDD cycles. Each cycle has a RED test, GREEN implementation, and REFACTOR step.

3. **Implement** — This is strict TDD. Claude writes the failing test first, runs it to confirm failure, then writes the minimum code to make it pass. Every commit follows the `[#N][RED|GREEN|REFACTOR]` format.

4. **Commit** — Feature branch, PR, and all CI gates must pass.

We enforced this with custom slash commands (`/explore-issue`, `/plan-issue`, `/tdd`) baked into CLAUDE.md. These acted as guardrails — Claude couldn't skip from exploring to implementing without going through the planning phase.

### What Worked Well

**The Explore phase was the highest-ROI investment.** Having Claude map out affected files, dependencies, and edge cases *before* writing any code prevented the classic AI-coding failure mode of generating plausible-looking code that misunderstands the existing architecture. One session caught that adding a new agent would require changes in seven files across three directories — information that would have taken 20 minutes to assemble manually.

**Pydantic AI's `TestModel` made agent testing practical.** Instead of mocking HTTP calls to LLM providers, we used Pydantic AI's test model to generate deterministic outputs matching our `result_type` schemas. This made agent unit tests fast, reliable, and actually useful for catching regressions.

**The CI pipeline as a safety net for AI-generated code.** Our 8-stage GitHub Actions pipeline — lint, type-check, tests, E2E, four security gates, Claude AI PR review, and deploy — caught issues that code review alone would miss. The security gates (pip-audit, npm audit, Gitleaks, Bandit) were especially valuable since AI-generated code can introduce dependency patterns you wouldn't choose yourself.

### What Surprised Me

**Claude Code was better at refactoring than greenfield code.** The REFACTOR phase of TDD — where the tests are green and the job is to clean up — played to Claude's strengths. It could see the working code, the test expectations, and the coding conventions all at once, and suggest simplifications that maintained correctness.

**Custom slash commands changed the collaboration dynamic.** Without them, it was too easy to say "just implement it." With `/explore-issue` enforcing a read-only exploration phase, the quality of the subsequent plan improved dramatically. The commands turned Claude from a code generator into something closer to a pair programmer who insists on understanding the problem first.

**Mutation testing revealed blind spots in AI-written tests.** We used `mutmut` to measure how well our test suite caught intentional bugs. The initial pass scored around 60% — many AI-written tests were testing the happy path but not edge cases. Targeting 80%+ forced a second round of test-writing that caught real bugs in boundary conditions for time calculations and schedule overlap detection.

## The Stack Decisions That Mattered

**Pydantic AI over LangChain:** Pydantic AI's type-safe approach — where agent inputs, outputs, and dependencies are all Pydantic models — eliminated an entire class of runtime errors. The `RunContext` dependency injection system kept agents testable without complex mock setups. And provider-agnostic config meant switching the Judge to a different LLM was a one-line change.

**Async-first backend:** Every database call, every agent invocation, and every external API call is async. This wasn't just good practice — it was essential for the parallel agent pipeline. `asyncio.gather` with per-agent error handling meant one slow Google Calendar API call couldn't block the entire review generation.

**Real database in tests:** Integration tests hit a real PostgreSQL instance (via Docker service container in CI). This caught issues that SQLite-based test databases would have hidden — timezone handling, JSONB query behavior, and concurrent write patterns.

## Security: OWASP Compliance in an AI Application

AI applications introduce security concerns beyond the standard web app checklist. FlowDay addresses these through four CI-enforced security gates (pip-audit, npm audit, Gitleaks, Bandit SAST), Fernet-encrypted OAuth tokens at rest, PII anonymization before any data reaches the LLM, and prompt injection defense through structured output schemas that constrain what the model can return.

The structured output approach was particularly effective for prompt injection defense. Because each agent's output must conform to a Pydantic schema — with specific field types, value ranges, and required fields — there's no open-ended text field where injected instructions could propagate through the pipeline.

## Looking Back

FlowDay demonstrated that building with AI agents isn't just about calling an API. The real work is in orchestration (parallel execution with error isolation), evaluation (cross-provider Judge with retry logic), and development process (AI-assisted TDD with strict phase gates).

The biggest lesson: the tooling around AI matters as much as the AI itself. Custom Claude Code commands, typed agent schemas, mutation testing, and a serious CI pipeline — these aren't glamorous, but they're what made the difference between a demo and something that actually works reliably.

If you're building a multi-agent system, start with the evaluation pipeline. The Judge agent was the last thing we designed but the first thing I'd build next time. Knowing whether your output is good — automatically, at scale — changes every decision upstream.

---

*FlowDay was built as part of CS 7180 (Special Topics in AI) at Northeastern University, Spring 2026. The source code is available on GitHub.*
