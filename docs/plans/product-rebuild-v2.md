# FlowDay v2 — Product Rebuild Plan

**Status**: Proposed
**Deadline context**: 2026-04-22 (~2 days from 2026-04-20)
**Philosophy**: Don't touch the backend core. Expose what's hidden, glue what's disconnected, delete what's confusing.

---

## 0. Problem Statement

The backend is feature-rich but product logic is broken:

1. **AI pipeline is a ghost** — the 6-agent orchestrator in `app/agents/` has zero HTTP endpoints. The most-advertised feature is unreachable.
2. **Three parallel time concepts confuse users** — Task / Schedule Block / Time Entry are stored separately with no cross-references. The user fills them redundantly and gets divergent views.
3. **No daily loop** — there's no single "home" that answers "what should I be doing right now?"
4. **Weekly Review page is an empty shell** — it fetches `/weekly-reviews` which returns 404.

---

## 1. Product Vision (one sentence)

> **FlowDay is an AI-coached work journal. You plan tomorrow in 2 minutes, work through the day with one-click timers on your plan, and get an AI narrative on Friday that you actually want to read.**

### The Loop (what a user does each day)

```
  Morning        →   Workday         →   Evening         →   End of week
  ─────────         ────────────        ─────────          ─────────────
  Open Plan         Open Today          Open Review        Open Weekly
  Drag tasks        Tap current         See planned        Generate narrative
  into hours        block → timer       vs actual          → AI coaches you
  (2 min)           starts              (30 sec)           (2 min read)
```

Everything else is either in service of this loop, or it gets cut.

---

## 2. Information Architecture (what pages exist)

### Final NavBar (5 items)

| Icon | Page | Route | Purpose |
|---|---|---|---|
| ⚡ | **Today** | `/` | Home. Live timeline of today's blocks + 1-tap timer. |
| 📅 | **Plan** | `/plan` | Drag tomorrow's tasks into time slots. |
| 📁 | **Projects** | `/projects` | Manage project/task library. |
| 📊 | **Review** | `/review` | Yesterday/today planned-vs-actual + AI daily summary. |
| 🧠 | **Weekly** | `/weekly` | AI narrative + judge scores + trend. |

### What changes vs. current frontend

- **Dashboard is deleted.** Its task-list UI moves into Projects; its timer moves into Today.
- **Planner is renamed Plan.** No behavior change except default-shows-tomorrow.
- **Today is new.** This is where users land after login.
- **Projects is extracted.** Was mixed into Dashboard.

---

## 3. Backend Additions (minimum required)

**Do not refactor existing endpoints.** Only add what's missing to connect the dots.

### 3.1 Weekly Review endpoints (P0 — unblocks core differentiation)

```
POST   /weekly-reviews/generate?week_start=YYYY-MM-DD
GET    /weekly-reviews/current?week_start=YYYY-MM-DD
GET    /weekly-reviews                          # history list
GET    /weekly-reviews/{id}                     # single review detail
```

`POST /weekly-reviews/generate`:
1. Calls `run_group_a(db, user_id, week_end_date)` (already exists)
2. Feeds result into `pattern_detector` → `narrative_writer` → `judge` (already exist)
3. Stores narrative + judge scores + agent_score_history rows (already exists)
4. Returns `{review_id, narrative, scores, generated_at}`

New table: **`weekly_reviews`**
```sql
id UUID PK
user_id UUID FK
week_start DATE
narrative TEXT
judge_scores_json JSONB   -- {actionability, accuracy, coherence}
agent_run_id UUID         -- ties to agent_score_history
generated_at TIMESTAMP
UNIQUE (user_id, week_start)
```

### 3.2 Daily Review endpoint (P1 — quick win for Review page)

```
POST   /daily-reviews/generate?date=YYYY-MM-DD
GET    /daily-reviews/current?date=YYYY-MM-DD
```

Lighter than weekly: runs only `time_analyst` + `narrative_writer` (skip Group A parallel, skip judge). Returns a 3-sentence "how was today?" blurb.

New table: **`daily_reviews`** (same shape as weekly but scoped to a date).

### 3.3 Start-timer context awareness (P1 — glue Schedule Block ↔ Time Entry)

Extend `POST /time-entries/start` response to include the **matching schedule block for now**, if any:

```json
{
  "id": "...",
  "task_id": "...",
  "started_at": "...",
  "matched_block_id": "abc-123"   // ← new, optional
}
```

Logic: when starting a timer for task X, look for a schedule_block where `task_id=X, date=today, start_hour <= now_hour < end_hour`. If found, return its id. Frontend uses this to highlight the active block on the Today timeline.

**No schema change needed.** Just a service-layer lookup.

### 3.4 User settings endpoints (P2 — nice to have, skip if short on time)

```
GET    /users/me/settings
PATCH  /users/me/settings
```

Reads/writes `users.settings_json`. Used for: work_hours_start/end, theme preference, default notification time.

---

## 4. Frontend Restructure

### 4.1 Page specs

#### 🏠 Today (`/`) — **new, becomes home**

**Layout**: Full-width vertical timeline (no sidebar).

- **Top bar**: current date + "Generate daily summary" button (calls `POST /daily-reviews/generate`)
- **Now indicator**: horizontal yellow line sliding across the timeline at real-time
- **Blocks**: pulled from `GET /schedule-blocks?date=today`
  - Past blocks: dimmed, show actual time entry overlay if tracked
  - **Current block**: highlighted yellow, has **"▶ Start"** button → calls `POST /time-entries/start` with that block's task_id
  - Active timer: block shows running elapsed time
  - Future blocks: normal
- **Empty state**: "No plan for today. [Go to Plan →]"
- **Unplanned time entries** (started without a block) show as ghost blocks in a different style

**API usage**: reuses `useScheduleBlocks` + `useStartTimer` + `useActiveTimer`. Zero new endpoints for base functionality.

#### 📅 Plan (`/plan`) — **renamed from Planner**

No structural changes. Just:
- Default selected date = **tomorrow** (currently defaults to today)
- Add a "Copy yesterday's plan" button (frontend-only: fetch yesterday's blocks, POST them with tomorrow's date)

#### 📁 Projects (`/projects`) — **extracted from Dashboard**

Two-column layout (same as current Dashboard minus timer).

- Left sidebar: project list + create
- Right: tasks for selected project + create/edit/delete
- **No timer here.** Timer only lives on Today.

#### 📊 Review (`/review`) — **mostly unchanged, add AI blurb**

Current planned-vs-actual comparison + weekly bar chart stays.

Add at top: **"AI daily summary"** section
- If `daily_reviews.current` exists → show it
- If not → **"Generate summary"** button
- Loading state: shows "Analyst agents are working…" with a subtle progress indicator

#### 🧠 Weekly (`/weekly`) — **wire up to real data, finally**

Current UI is fine. Just swap fake endpoint for real:
- `GET /weekly-reviews/current` → populates narrative + radar + trend chart
- **"Generate new weekly review"** button (prominent) → calls `POST /weekly-reviews/generate`
- While generating: show the **4 Group A agents running in parallel** as animated chips, then Pattern Detector → Narrative Writer → Judge sequentially. (This is the one place to brag about the architecture.)

### 4.2 Components to add

- `components/TodayTimeline.tsx` — reuse `TimelineGrid.tsx` but with "now line" + start-timer buttons per block
- `components/NowIndicator.tsx` — thin yellow line with live clock, updates every 30s
- `components/AgentPipelineIndicator.tsx` — shows 4 parallel + 3 sequential agent status during generation
- `components/GenerateReviewButton.tsx` — shared between Review and Weekly pages

### 4.3 Components to delete

- Everything currently in `pages/DashboardPage.tsx` that mixes project/task/timer — splits into Projects + Today
- `useTimerBootstrap` stays, but move from App-level into Today page only (stops the infinite `/time-entries` polling when user isn't on Today)

---

## 5. Implementation Phases (TDD, respecting workflow rules)

Following `claude-project-instructions.md`: Explore → Plan → Implement (RED/GREEN/REFACTOR) → Commit.

### Phase A — Backend: Expose the AI pipeline (~6h)

**Issue #A1: Weekly reviews endpoints + table**

- RED: write failing test `test_post_weekly_reviews_generate_returns_narrative`
- RED: `test_weekly_reviews_table_exists` (alembic migration)
- GREEN: alembic migration for `weekly_reviews` table
- GREEN: `services/weekly_review_service.py` orchestrating Group A→B→C→D and persisting
- GREEN: `api/weekly_reviews.py` with 4 routes
- GREEN: `schemas/weekly_review.py`
- REFACTOR: extract pipeline call from service; add structured logging + Grafana metric `weekly_review_generated_total`
- Mutation testing: `mutmut run` on the new service

**Issue #A2: Daily reviews endpoints + table** (analogous, cheaper)

**Issue #A3: Add `matched_block_id` to time-entries/start response**

- RED: test that starting a timer during an existing block returns matched_block_id
- GREEN: add lookup in `time_entry_service.start_timer`
- No schema change

### Phase B — Frontend: Wire Weekly page (~3h)

**Issue #B1: Real weekly review data flow**

- RED: `WeeklyReviewPage.test.tsx` — mock `/weekly-reviews/current`, assert narrative renders
- RED: test "Generate" button triggers POST
- GREEN: add `api/weeklyReviews.ts` hooks
- GREEN: replace placeholder data in `WeeklyReviewPage.tsx`
- GREEN: add `AgentPipelineIndicator` loading state
- REFACTOR: extract shared `GenerateReviewButton`

### Phase C — Frontend: Build Today + restructure nav (~6h)

**Issue #C1: Today page**

- RED: `TodayPage.test.tsx` — renders today's blocks, shows now-line, start button on current block
- GREEN: `pages/TodayPage.tsx`, `components/NowIndicator.tsx`
- GREEN: extend `ScheduleBlockItem` with read-only "▶ Start" variant
- REFACTOR: share timeline math with Plan page

**Issue #C2: Extract Projects page, update NavBar, set Today as /**

- RED: routing tests — `/` renders TodayPage, `/projects` renders ProjectsPage
- GREEN: move project/task UI out of DashboardPage into ProjectsPage
- GREEN: update App.tsx routes; delete DashboardPage
- GREEN: NavBar: replace 4 items with 5 (Today / Plan / Projects / Review / Weekly)
- REFACTOR: run `npm run lint` + ensure all prior tests still pass

### Phase D — Frontend: Wire Daily Review (~2h)

**Issue #D1: AI daily summary on Review page**

- RED: Review page test — generate button calls daily-reviews POST, result renders
- GREEN: `api/dailyReviews.ts`, new "AI summary" section in `ReviewPage`

### Phase E — Polish & Ship (~3h)

- Fix the `/time-entries` infinite-loop bug (move `useTimerBootstrap` into Today only)
- Run full test suite: `pytest` backend, `npx vitest` frontend, `npm run build`
- `mutmut run` on backend agents service (target ≥80%)
- Deploy: backend Docker → whatever host, frontend → Vercel
- Smoke-test the happy path end-to-end

### Total estimate: ~20h over 2 days. Tight but doable if scope holds.

---

## 6. What's Explicitly OUT of Scope

**Cut ruthlessly.** Touching any of these risks the deadline:

- ❌ Rewriting the drag-drop library
- ❌ Mobile responsive redesign
- ❌ Dark/light theme toggle (dark-only, per CLAUDE.md)
- ❌ Notifications (push or email)
- ❌ Collaboration / team features
- ❌ New agent types
- ❌ Changing the color palette (already chosen)
- ❌ Realtime websockets / live-sync across tabs
- ❌ Natural language task input ("remind me to…")
- ❌ User-facing error analytics beyond Sentry
- ❌ Changing OAuth providers or auth flow

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Agent pipeline fails on real data (was only tested with `TestModel`) | High | High | Do Phase A end-to-end integration test with a seeded user before building frontend on top |
| Judge retries timeout | Medium | Medium | Set hard 30s timeout on `POST /weekly-reviews/generate`; return 202 + background job if slow |
| Vercel deploy misconfigured env vars | Medium | High | Deploy a dummy build to Vercel at start of Day 1, not end of Day 2 |
| `mutmut` score < 80% blocks merge | Medium | Low | Run it early; raise issues as separate cleanup PRs, not blocking |
| Frontend tests break on route restructure | High | Low | Update tests alongside route changes in same commit |

---

## 8. Success Criteria (how we know v2 shipped)

1. ✅ Cold-start user can log in → land on Today → see a usable empty state that points to Plan.
2. ✅ User can drag a task into Plan, come back to Today, see the block, tap ▶, timer runs.
3. ✅ User clicks "Generate weekly review" → sees the 7-agent pipeline indicator → gets a real AI-written paragraph with judge scores.
4. ✅ All existing backend tests still pass.
5. ✅ All existing frontend tests still pass (after route/store updates).
6. ✅ `npm run build` + `docker build` both succeed.
7. ✅ Deployed to Vercel + Docker host, reachable over HTTPS.
8. ✅ At least one end-to-end Playwright test covers the Plan → Today → Timer → Review loop.

---

## 9. Decision Points for the User (before coding)

Before I start TDD, please confirm:

1. **Is "Today" as the homepage the right call?** (vs. keeping Dashboard feel)
2. **Daily reviews** — P1 (build) or cut? They take maybe 2 hours but aren't strictly needed if weekly works.
3. **Auto-link timer to block** (Phase A #A3) — P1 (build) or cut? Without it, Today page can still work but won't highlight the "live" block during active timer.
4. **Copy-yesterday's-plan button** — P2 (build) or cut? Pure UX sugar.
5. **Daily/weekly reviews stored per-user-per-date** — is one re-generate per day acceptable, or should users be able to regenerate multiple versions?

Once you answer these 5, I can start Phase A with `/explore-issue` → `/plan-issue` → `/tdd` per the project workflow.
