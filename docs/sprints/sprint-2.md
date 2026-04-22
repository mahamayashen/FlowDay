# Sprint 2

**Duration:** 2026-04-15 – 2026-04-17  
**Sprint Goal:** Build the scheduling and time-tracking layer — ScheduleBlock, TimeEntry, analytics endpoints, and observability dashboards.

---

## Planning

### Team

| Member | Focus Area |
|--------|------------|
| @EvanjyChen | ScheduleBlock, TimeEntry, analytics, ExternalSync, Grafana |
| @mahamayashen | Integration tests, code review |

### Issues Committed

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #19 | Implement ScheduleBlock model and CRUD API | @EvanjyChen | Done |
| #20 | Implement TimeEntry model and CRUD API | @EvanjyChen | Done |
| #21 | Add Planned vs Actual comparison endpoint | @EvanjyChen | Done |
| #22 | Add weekly aggregation and stats endpoint | @EvanjyChen | Done |
| #23 | Implement ExternalSync model and base sync framework | @EvanjyChen | Done |
| #24 | Write integration tests for scheduling and time tracking | @EvanjyChen | Done |
| #25 | Set up Grafana dashboards and AI metrics scaffolding | @EvanjyChen | Done |

### Acceptance Criteria Summary

- ScheduleBlock CRUD: create/read/update/delete time blocks linked to tasks, with overlap validation
- TimeEntry CRUD: start/stop timer entries, calculate durations, prevent overlapping active entries
- Planned vs Actual endpoint: compare scheduled hours vs actual hours per project/task
- Weekly stats endpoint: aggregate hours, completion rates, productivity metrics for a given week
- ExternalSync model: track sync status for Google Calendar and GitHub integrations
- Grafana: dashboards for API latency, error rates, and AI agent metrics (scaffolded via Prometheus)
- Integration tests: cover scheduling conflict edge cases, time entry boundary conditions

### Risks / Dependencies

- ScheduleBlock and TimeEntry both depend on Task model from Sprint 1
- Grafana dashboards require Prometheus metrics to be instrumented in the app

### Definition of Done

- All tests pass, lint clean, type-check clean
- TDD commit format enforced
- PR reviewed and merged to `main`
- Property-based tests (`hypothesis`) for analytics calculations

---

## Retrospective

**Issues Completed:** 7 / 7  
**PRs Merged:** #51, #52, #53, #54, #55

### What Went Well

- **Fast, focused sprint** — 7 issues completed in 2 days. Shorter sprint length kept momentum high (action item from Sprint 1 retro).
- **Property-based testing with hypothesis** — used `@given` strategies for analytics edge cases (zero-duration entries, overlapping time ranges), which found a real bug: zero-duration time entries were inflating actual hours.
- **Grafana + Prometheus scaffolding** — metrics infrastructure landed early, making it easy to add counters/histograms in later sprints.
- **Hotfixes shipped quickly** — PRs #54 and #55 fixed analytics bugs found by hypothesis tests. The TDD cycle caught these before they reached main.

### What Didn't Go Well

- **Unplanned work** — 2 hotfix PRs (#54, #55) were needed for analytics edge cases. Should have written more boundary tests upfront.
- **No frontend progress** — still 100% backend. Frontend scaffold (#35) was not started.
- **ExternalSync model is a stub** — #23 landed the model and framework but no actual sync logic. Risk of scope creep in Sprint 3.

### Action Items for Next Sprint

- [ ] Start frontend scaffold (#35) to unblock UI development
- [ ] Begin AI agent pipeline (Groups A–D) — the core differentiator
- [ ] Implement OAuth integrations (Google Calendar, GitHub) to feed agent data
- [ ] Use worktrees for parallel backend/frontend development
- [ ] Add `hypothesis` tests for all new service-layer logic
