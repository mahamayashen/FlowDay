# Reflection: Building FlowDay with Claude Code

## How Claude Code Changed My Development Process

Before this project, my experience with AI coding assistants was autocomplete on steroids — helpful for boilerplate, unreliable for anything architectural. Claude Code fundamentally changed that dynamic, and the difference came down to one thing: **structure**.

We defined a strict 4-phase workflow (Explore → Plan → Implement → Commit) and encoded it as custom slash commands in CLAUDE.md. The `/explore-issue` command forced Claude into a read-only mode where it mapped affected files and dependencies before touching anything. This single constraint was the highest-impact decision of the project. Without it, Claude would generate plausible code that missed context — a new endpoint that duplicated logic already in the service layer, or a test that mocked the wrong dependency. With the explore phase, Claude understood the existing architecture before proposing changes, and the resulting code actually fit.

## Specific Claude Code Insights

**CLAUDE.md as a living contract.** Our CLAUDE.md file grew to include architecture decisions, naming conventions, security requirements, and explicit "don'ts" (like never mocking PostgreSQL in integration tests). Every session started with Claude reading this file, which meant institutional knowledge persisted across sessions even when context windows reset. The file became the project's source of truth — not just for Claude, but for us as developers.

**Custom slash commands enforced discipline we wouldn't maintain ourselves.** The `/tdd` command implemented strict RED-GREEN-REFACTOR cycles with automatic commit message formatting. Left to our own devices, we would have skipped the RED phase ("I know the test will fail, let me just write the code"). Claude enforced it mechanically, and the result was better test coverage and fewer regressions. The commit history became a readable narrative of every feature's development.

**The explore phase caught architectural misunderstandings early.** When implementing the Judge agent, the explore phase revealed that the existing agent base class assumed synchronous execution — meaning the Judge couldn't be naively added to the pipeline without refactoring the orchestrator. A human developer might have discovered this mid-implementation after writing 200 lines of code. Claude surfaced it in the first two minutes of exploration.

**Mutation testing exposed the limits of AI-written tests.** Claude writes tests that pass and cover the stated requirements, but `mutmut` revealed that many of those tests wouldn't catch subtle bugs — off-by-one errors in time calculations, missing boundary checks on schedule overlaps. Our initial mutation score was around 60%. Targeting 80% required a deliberate second pass where we asked Claude to think adversarially about its own test suite. This was a powerful feedback loop: AI writes code, AI writes tests, mutation testing proves the tests are insufficient, AI improves the tests with specific guidance about what mutations survived.

## What I'd Do Differently

I would invest more in the CLAUDE.md file from day one. We built it incrementally as we hit problems, but front-loading the architecture decisions, error handling patterns, and testing conventions would have prevented several false starts in early sessions. The file is cheap to write and pays dividends on every subsequent interaction.

I would also build the evaluation pipeline (Judge agent) first. Having automated quality scoring early would have given us a feedback signal for every other agent in the pipeline, rather than relying on manual review until the Judge was implemented in a later sprint.

**Mutation testing needs an effort budget.** One practical lesson: mutation testing is computationally expensive. Running `mutmut` across the entire codebase took significant time, and not every module deserves the same level of scrutiny. In hindsight, I would introduce an *effort parameter* for mutation testing — critical modules like the agent orchestrator, the Judge scoring logic, and time calculation utilities should run at full mutation effort (all operators, no sampling), while less critical modules like simple CRUD endpoints or UI utility functions could run at reduced effort (fewer mutation operators, or a random sample of mutants). This tiered approach would preserve the quality signal where it matters most while keeping CI cycle times reasonable. It's a resource allocation problem: mutation testing budget should follow the risk profile of the code, not be spread uniformly.

## The Bigger Picture

Claude Code isn't a replacement for engineering judgment — it's an amplifier. The strict workflow, the custom commands, the living CLAUDE.md file — these are all structures we designed to channel Claude's capabilities toward reliable output. Without them, the same tool produces inconsistent results. The lesson generalizes: AI-assisted development is a *systems design* problem, not just a prompting problem. The quality of the output depends on the quality of the process around it.

---

*Word count: ~550*
