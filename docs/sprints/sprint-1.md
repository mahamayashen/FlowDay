# Sprint 1

**Duration:** 2026-03-22 – 2026-04-15  
**Sprint Goal:** Stand up the backend foundation — database, auth, core CRUD APIs, CI pipeline, and monitoring.

---

## Planning

### Team

| Member | Focus Area |
|--------|------------|
| @mahamayashen | Backend foundation, infrastructure, CI |
| @EvanjyChen | Claude Code config (CLAUDE.md, skills, hooks), project setup |

### Issues Committed

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #1 | Set up FastAPI app skeleton and project structure | @mahamayashen | Done |
| #2 | Configure PostgreSQL + SQLAlchemy async + Alembic migrations | @mahamayashen | Done |
| #3 | Implement User model and OAuth 2.0 + JWT auth | @mahamayashen | Done |
| #4 | Implement Project model and CRUD API | @mahamayashen | Done |
| #5 | Implement Task model and CRUD API | @mahamayashen | Done |
| #6 | Set up Docker Compose for local development | @mahamayashen | Done |
| #7 | Configure GitHub Actions CI pipeline | @mahamayashen | Done |
| #8 | Add Sentry error tracking and health monitoring | @mahamayashen | Done |
| #9 | Write integration tests for Project and Task CRUD | @mahamayashen | Done |

### Acceptance Criteria Summary

- FastAPI skeleton responds on `/health` with DB + Redis status
- User model supports OAuth upsert, Fernet-encrypted tokens, JWT access/refresh
- Project and Task CRUD endpoints are user-scoped with ownership checks
- Docker Compose provides PostgreSQL 16 + Redis 7 with health checks
- GitHub Actions CI runs: lint (ruff), type-check (mypy), tests (pytest), security scan (pip-audit), Docker build
- Sentry captures errors with breadcrumbs; `/health/detailed` reports DB/Redis latency
- Integration tests hit a real test database (no mocks)

### Risks / Dependencies

- OAuth callback URLs must be configured in Google/GitHub developer consoles before #3 can be fully tested
- Docker Compose must be up before integration tests can run in CI (handled via service containers)

### Definition of Done

- All tests pass (`pytest -x -q`)
- Lint clean (`ruff check . && ruff format .`)
- Type-check clean (`mypy .`)
- TDD commit format: `[#N][RED|GREEN|REFACTOR] description`
- PR reviewed and merged to `main`

---

## Retrospective

**Issues Completed:** 9 / 9  
**PRs Merged:** #10, #11, #12, #13, #14, #15, #16

### What Went Well

- **TDD discipline established early** — every feature started with `[RED]` failing tests, then `[GREEN]` implementation, then `[REFACTOR]`. This became the team norm from day one.
- **CLAUDE.md and skills set up early** — having `CLAUDE.md` with `@imports` for DATA_MODEL.md and CONVENTIONS.md kept Claude Code aligned with project decisions. Custom skills (`/review-pr`, `/review-pr-v2`) saved time on PR reviews.
- **Real database testing** — integration tests hit a real PostgreSQL instance (via Docker Compose test service on port 5433), catching migration issues that mocks would have missed.
- **CI pipeline green from the start** — GitHub Actions with lint + type-check + tests + security scan + Docker build caught issues before merging.
- **Mutation testing adoption** — `mutmut` configured early, targeting ≥80% mutation score, which pushed us to write stronger assertions.

### What Didn't Go Well

- **OAuth callback testing was painful** — Google/GitHub OAuth flows are hard to test in CI without real credentials. Ended up mocking at the HTTP layer but it felt fragile.
- **Sprint was too long** — 3+ weeks for the foundation sprint meant context drift. Shorter sprints would help maintain focus.
- **No frontend work started** — all 9 issues were backend. Should have scaffolded the frontend in parallel.
- **Assignees not set on all issues** — only @mahamayashen was assigned; @EvanjyChen's contributions (CLAUDE.md, skills, hooks) weren't tracked as issues.

### Action Items for Next Sprint

- [ ] Keep sprints to ~3 days to maintain momentum
- [ ] Start frontend scaffold early to unblock UI work
- [ ] Assign both team members on issues to reflect actual work
- [ ] Use property-based testing (`hypothesis`) for core logic
- [ ] Add hooks to enforce commit format automatically (PreToolUse hook)
