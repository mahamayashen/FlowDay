# Sprint 4

**Duration:** 2026-04-19 – 2026-04-22 (final sprint)  
**Sprint Goal:** Ship the frontend, deploy to production, add E2E tests, security audit, and complete all deliverables.

---

## Planning

### Team

| Member | Focus Area |
|--------|------------|
| @EvanjyChen | Frontend UI pages, E2E tests, CI/CD enhancements |
| @mahamayashen | Frontend redesign, production deployment, security audit, documentation |

### Issues Committed

#### Frontend

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #35 | Set up React app scaffold with Vite + TypeScript | @EvanjyChen | Done |
| #36 | Implement auth flow UI | @EvanjyChen | Done |
| #37 | Build project and task management views | @EvanjyChen | Done |
| #38 | Build daily planner with drag-and-drop | @EvanjyChen | Done |
| #39 | Build inline timer component | @EvanjyChen | Done |
| #40 | Build Planned vs Actual view | @EvanjyChen | Done |
| #41 | Build weekly review display page | @EvanjyChen | Done |

#### Production & Infrastructure

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #81 | Add CORS middleware + BACKEND_CORS_ORIGINS config | @mahamayashen | Done |
| #82 | Frontend: use VITE_API_BASE_URL for all API calls | @mahamayashen | Done |
| #83 | Add Railway deployment config + migration hook | @mahamayashen | Done |
| #84 | Provision Railway project + Postgres + Redis | @mahamayashen | Done |
| #78 | Install Claude Code GitHub App for AI Review | @EvanjyChen | Done |
| #44 | Configure production Docker build and deploy | — | Open |

#### Testing & Security

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #43 | Write end-to-end tests (Playwright) | — | Open |
| #42 | Conduct security audit and OWASP compliance | — | Open |

#### Carried Over from Sprint 3

| Issue | Title | Assignee | Status |
|-------|-------|----------|--------|
| #33 | Add PII anonymization layer for LLM calls | — | Open |
| #34 | Write AI agent tests (unit + integration) | — | Open |
| #73 | Plumb token usage into WeeklyReview metadata | — | Open |

### Acceptance Criteria Summary

- All 7 frontend pages functional: login, projects, tasks, daily planner, timer, planned-vs-actual, weekly review
- Frontend redesign: consistent design system with brand colors (#FFDE42, #53CBF3, #5478FF, #111FA2)
- App deployed on Railway with public URL, PostgreSQL, and Redis
- CORS configured for frontend ↔ backend communication
- At least 1 Playwright E2E test covering a critical user flow
- Security audit: gitleaks, npm audit, OWASP checklist, SAST scan
- CI pipeline: all 8 stages green (lint, typecheck, test, E2E, security, AI review, preview, prod deploy)

### Risks / Dependencies

- Railway deployment needs environment variables (DB URL, Redis, OAuth secrets, JWT key)
- E2E tests need deployed frontend + backend to test full flows
- Claude Code GitHub App must be installed for AI PR review stage
- Time pressure: this is the final sprint before submission deadline

### Definition of Done

- App accessible via public URL
- CI pipeline fully green
- All deliverables ready: README, blog post, video demo, reflections
- C.L.E.A.R. reviews on at least 2 PRs
- AI disclosure metadata on PR descriptions

---

## Retrospective

**Issues Completed:** ___ / ___  
**PRs Merged:** #61, #63, #64, #65, #67, #68, #69, #71, #74, #75, #80, #87, #88, #89, #90, ...

> **Note:** Fill in final counts after sprint close.

### What Went Well

- **Frontend shipped fast** — 7 UI pages (#35–#41) landed in ~2 days with full TDD (RED/GREEN/REFACTOR). React + Vite + TypeScript scaffold enabled rapid iteration.
- **Frontend redesign polished the UI** — PR #71 brought a cohesive design system (#FFDE42/#53CBF3/#5478FF/#111FA2 palette), real API wiring, and full CRUD interactions. Portfolio-worthy quality.
- **Railway deployment configured** — CORS, `VITE_API_BASE_URL`, Railway config, and migration hooks all landed via PRs #87–#90.
- **Claude Code GitHub App installed** — AI PR review (Stage 6) is now available in CI.
- **PR template + CODEOWNERS added** — PR #74 added C.L.E.A.R. self-review checklist; PR #75 added CODEOWNERS and issue templates. Process improvements that pay off immediately.

### What Didn't Go Well

- _Fill in after sprint close_

### Action Items (Post-Sprint / Submission)

- [ ] Verify production deployment is accessible
- [ ] Complete E2E tests (#43) and security audit (#42)
- [ ] Write README with Mermaid architecture diagram
- [ ] Publish blog post
- [ ] Record 5-10 min video demo
- [ ] Write individual reflections (500 words each)
- [ ] Submit Google Form showcase
