# /plan-issue — Phase 2: Plan Before Implementing

You are creating an implementation plan for a FlowDay issue. This plan will be saved to `docs/plans/` and must be approved before any code is written.

## Input

The user will provide: issue number, description, and optionally the explore summary from Phase 1.
If not provided, ask: "Which issue number? Have you run /explore-issue first?"

## Rules

- **NO implementation code** — planning only
- Output goes to `docs/plans/issue-<N>-<short-name>.md`
- Each acceptance criterion maps to exactly ONE TDD cycle
- Get user confirmation before proceeding to /tdd

## Plan Structure

Write the plan document with this exact structure:

```markdown
# Issue #N — <Title>

## Phase 1: Explore

### What exists
- <from explore phase or scan now>

### Impact analysis
- <files affected, dependencies>

---

## Phase 2: Plan

### Acceptance criteria
1. <criterion 1 — one testable behavior>
2. <criterion 2>
3. ...

### Cycle 1 — <criterion 1 description>

**RED tests** (`tests/<path>/test_<module>.py`):
- `test_<what>_<expected>` — <what it asserts>
- `test_<what>_<expected>` — <what it asserts>

**GREEN implementation**:
- `app/<path>/<module>.py` — <what to create/modify>
- <any other files>

**REFACTOR**:
- <what to clean up>

### Cycle 2 — <criterion 2 description>
<same structure>

### Post-implementation
- Run `ruff check . && ruff format .`
- Run `mutmut run --paths-to-mutate=app/<module>.py`
- Target: ≥ 80% mutation score
- Open PR `feature/<N>-<name> → main`, link Issue #N
```

## Branch Setup

Before presenting the plan, create the feature branch:
```
git checkout -b feature/<N>-<short-name>
```

## Confirmation

After writing the plan, ask the user:
"Plan saved to `docs/plans/issue-<N>-<name>.md`. Review the acceptance criteria and cycles. Ready to start /tdd?"

Do NOT proceed to implementation without explicit user approval.
