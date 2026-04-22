# Sprint 3

**Duration:** 2026-04-17 – 2026-04-20  
**Sprint Goal:** Build the full AI agent pipeline (Groups A–D), OAuth integrations, and the WeeklyReview orchestration endpoint.

---

## Planning

### Team

| Member | Focus Area |
|--------|------------|
| @EvanjyChen | AI agents (Groups A–D), OAuth integrations, frontend scaffold + UI pages |
| @mahamayashen | WeeklyReview model + endpoint, frontend redesign, code review |

### Issues Committed

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #26 | Implement Google Calendar OAuth integration | @EvanjyChen | Done |
| #27 | Implement GitHub OAuth integration | @EvanjyChen | Done |
| #28 | Implement AI Agent Group A: parallel analysts | @EvanjyChen | Done |
| #29 | Implement AI Agent Group B: Pattern Detector | @EvanjyChen | Done |
| #30 | Implement AI Agent Group C: Narrative Writer | @EvanjyChen | Done |
| #31 | Implement AI Agent Group D: Judge (LLM-as-Judge) | @EvanjyChen | Done |
| #32 | Implement WeeklyReview model and orchestration endpoint | @mahamayashen | Done |
| #33 | Add PII anonymization layer for LLM calls | — | Open |
| #34 | Write AI agent tests (unit + integration) | — | Open |
| #73 | Plumb token usage and retry count into WeeklyReview metadata | — | Open |

### Acceptance Criteria Summary

- Google Calendar OAuth: token exchange, encrypted storage, calendar event sync
- GitHub OAuth: token exchange, commit/PR data retrieval
- Agent Group A (Time, Meeting, Code, Task analysts): run in parallel via `asyncio.gather`, each returns structured analysis
- Agent Group B (Pattern Detector): consumes Group A outputs, identifies productivity patterns
- Agent Group C (Narrative Writer): generates human-readable weekly narrative from patterns
- Agent Group D (Judge / LLM-as-Judge): scores narrative quality using a **different LLM provider** (Gemini), retries if below threshold
- WeeklyReview model: status enum (pending → generating → complete/failed), JSONB columns for narrative, insights, metadata
- WeeklyReview endpoint: `POST /weekly-reviews` triggers full A→D pipeline, `GET /weekly-reviews/{week_start}` returns stored review

### Risks / Dependencies

- Agent Group D must use a different LLM provider than Group C (Gemini vs OpenAI) — provider isolation is a hard requirement
- Pipeline orchestration (A→B→C→D) must handle partial failures gracefully
- #33 (PII anonymization) and #34 (agent tests) may slip to Sprint 4

### Definition of Done

- All tests pass with TDD discipline
- Agent tests use Pydantic AI `TestModel` (no real LLM calls in CI)
- Mutation testing ≥80% for service layer
- Security: OAuth tokens encrypted at rest (Fernet)

---

## Retrospective

**Issues Completed:** 7 / 10 (3 carried over to Sprint 4)  
**PRs Merged:** #56, #57, #58, #59, #60, #62, #66, #70, #72

### What Went Well

- **Full AI pipeline landed** — all 4 agent groups (A→B→C→D) implemented and tested. The parallel `asyncio.gather` for Group A and LLM-as-Judge with provider isolation (Gemini) are working.
- **LLM-as-Judge pattern** — Group D uses `google-gla:gemini-1.5-flash` (different provider from Narrative Writer), with `ModelRetry` for scores below threshold. Histogram and counter metrics integrated for observability.
- **Both teammates contributing PRs** — @EvanjyChen handled agents and initial frontend, @mahamayashen handled WeeklyReview model/endpoint and frontend redesign. Parallel progress on backend and frontend.
- **`/review-pr-v2` skill proved valuable** — caught several issues: missing DB-level constraints on judge scores, phantom metric observations before `db.flush()`, and dead code. The v2 skill added dependency audit and test coverage gap detection over v1.
- **OAuth integrations solid** — Google Calendar and GitHub OAuth with encrypted token storage landed cleanly.

### What Didn't Go Well

- **3 issues carried over** — #33 (PII anonymization), #34 (agent tests), and #73 (token usage plumbing) didn't make it. These are important for security and observability.
- **Frontend and backend developed sequentially, not in parallel** — despite the retro action item to use worktrees, we still worked on one branch at a time.
- **Agent test coverage is thin** — agents are tested with `TestModel` but more edge cases are needed (empty data, API failures, timeout scenarios).
- **No C.L.E.A.R. framework on PR reviews** — PR reviews happened but didn't follow the structured C.L.E.A.R. format. Need to adopt this for remaining PRs.

### Action Items for Next Sprint

- [ ] Adopt C.L.E.A.R. framework for all PR reviews going forward
- [ ] Use worktrees for parallel feature development (E2E tests + security audit)
- [ ] Complete carried-over issues (#33, #34, #73)
- [ ] Add Playwright E2E tests
- [ ] Set up production deployment
- [ ] Add AI disclosure metadata to PR descriptions
