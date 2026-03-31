# /explore-issue — Phase 1: Explore Before Building

You are in EXPLORE mode for a FlowDay issue. Your goal is to understand the codebase impact BEFORE any changes are made.

## Input

The user will provide: issue number and description.
If not provided, ask: "Which issue number and what does it involve?"

## Rules

- **NO file edits allowed** — read-only exploration
- Use `Read`, `Glob`, `Grep`, `git log`, `git diff` only
- Enter plan mode to prevent accidental edits

## Steps

### 1. Understand the Issue
- What feature/fix does this issue require?
- Which of the 4 production requirements does it connect to? (parallel agents, LLM-as-Judge, CI/CD+monitoring, security)

### 2. Scan Affected Code
- Read relevant files in `backend/app/` (models, services, api, schemas, core)
- Check `backend/tests/` for existing test coverage
- Read `docs/DATA_MODEL.md` for entity relationships
- Check `alembic/versions/` for existing migrations

### 3. Identify Dependencies
- What existing modules does this issue depend on?
- What other issues must be completed first?
- Are there missing pip dependencies needed?

### 4. Impact Analysis
Document:
- **Files to create:** list new files needed
- **Files to modify:** list existing files that need changes
- **Database changes:** any new models, migrations, or indexes
- **Test files needed:** where tests should live (mirror app structure)
- **External dependencies:** any new packages to add to pyproject.toml

### 5. Output Summary

Present findings as a structured summary:

```
## Issue #N — Explore Summary

### What exists
- <existing relevant code>

### What's needed
- <new code/files required>

### Impact analysis
- <files affected, dependencies, risks>

### Missing dependencies
- <any packages to install>

### Ready for Phase 2?
- [ ] All dependencies met
- [ ] Scope is clear
- [ ] No blockers identified
```

After presenting the summary, ask: "Ready to move to /plan-issue?"
