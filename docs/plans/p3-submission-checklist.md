# P3 Submission Checklist & Priority Plan

**Date:** 2026-04-20 | **Due:** Wednesday 2:59am | **Current Score Estimate:** ~105-130 / 200

---

## Score Summary

| Category | Max | Current | After Fixes | Key Gaps |
|---|---|---|---|---|
| Application Quality | 40 | ~20 | 35-40 | No deployment |
| Claude Code Mastery | 55 | ~30 | 50-55 | No MCP, agents, worktrees, C.L.E.A.R. |
| Testing & TDD | 30 | ~24 | 30 | No Playwright E2E |
| CI/CD & Production | 35 | ~18 | 30-35 | No deploy, AI review, security gates |
| Team Process | 25 | ~15 | 22-25 | No sprint docs, standups, C.L.E.A.R. |
| Documentation & Demo | 15 | ~0 | 12-15 | Everything missing |
| **Bonus** | +10 | +6 | +6 | hypothesis (+3), mutmut (+3) already done |
| **Total** | 200+10 | ~113 | ~185-200+6 | |

---

## Phase 1: CRITICAL — Infrastructure (do first)

### 1.1 Deploy to public URL
- [ ] Choose platform (Vercel, Railway, Fly.io, or Render)
- [ ] Configure frontend build + backend deployment
- [ ] Set environment variables (DB, Redis, OAuth, JWT secrets)
- [ ] Verify app loads at public URL
- [ ] **SCREENSHOT:** App running on public URL
- **Points at risk:** ~20 pts across App Quality + CI/CD

### 1.2 Add `.mcp.json` to repo root
- [ ] Create `.mcp.json` with at least 1 MCP server (Playwright is already in local settings)
- [ ] Commit to repo so it's visible as shared config
- [ ] Use MCP tool in a session (e.g., `browser_navigate` to test deployed app)
- [ ] **SCREENSHOT:** MCP tool being called in Claude Code session
- **Points at risk:** ~5-8 pts in Claude Code Mastery

### 1.3 Create `.claude/agents/` with at least 1 agent
- [ ] Create `.claude/agents/security-reviewer.md` (or similar)
- [ ] Run the agent on a real PR or code change
- [ ] **SCREENSHOT:** Agent output in session
- **Points at risk:** ~5-8 pts in Claude Code Mastery

---

## Phase 2: HIGH — Testing & CI/CD

### 2.1 Add Playwright E2E test (at least 1)
- [ ] Install Playwright in frontend (`npm init playwright@latest`)
- [ ] Write 1 E2E test for a critical user flow (e.g., login → dashboard → create task)
- [ ] Verify it runs locally
- [ ] Add E2E stage to `.github/workflows/ci.yml`
- **Points at risk:** ~8 pts across Testing + CI/CD

### 2.2 Add security gates to CI (need 4+ total)
- [ ] Gate 1: pip-audit (ALREADY DONE)
- [ ] Gate 2: Add `npm audit` step for frontend dependencies
- [ ] Gate 3: Add gitleaks or trufflehog for pre-commit secret detection
- [ ] Gate 4: Add SAST — use security-reviewer agent or bandit for Python
- [ ] Gate 5 (optional): Add OWASP dependency-check
- **Points at risk:** ~8 pts in CI/CD

### 2.3 Add AI PR review to CI
- [ ] Add `claude-code-action` or `claude -p` step in GitHub Actions
- [ ] Trigger on PR events
- **Points at risk:** ~3-5 pts in CI/CD

### 2.4 Add deploy stages to CI
- [ ] Preview deploy on PR (Vercel preview or equivalent)
- [ ] Production deploy on merge to main
- **Points at risk:** ~5 pts in CI/CD

### 2.5 Add frontend lint/test to CI
- [ ] Add ESLint + TypeScript check (`tsc --noEmit`) step
- [ ] Add `npx vitest run` step
- **Points at risk:** ~3 pts in CI/CD

### 2.6 OWASP Top 10 in CLAUDE.md
- [ ] Add OWASP Top 10 awareness section to CLAUDE.md or CONVENTIONS.md
- [ ] Document which OWASP risks are mitigated and how
- **Points at risk:** ~2 pts in CI/CD

---

## Phase 3: HIGH — Claude Code Mastery Evidence

### 3.1 Worktree parallel development
- [ ] Use `git worktree add` to create 2 worktrees for 2 different features
- [ ] Develop both features in parallel (even small ones)
- [ ] Commit from both worktrees so git history shows parallel branches
- [ ] **SCREENSHOT:** `git worktree list` showing 2+ active worktrees
- [ ] **SCREENSHOT:** Git branch graph showing parallel development
- **Points at risk:** ~5 pts in Claude Code Mastery

### 3.2 Writer/Reviewer pattern + C.L.E.A.R. on 2+ PRs
- [ ] On 2 PRs: have one Claude session write the code, another review it
- [ ] Apply C.L.E.A.R. framework in PR review comments:
  - **C**ontext: What does this PR do?
  - **L**ogic: Are there logic errors?
  - **E**dge cases: What could go wrong?
  - **A**lternatives: Better approaches?
  - **R**eadability: Is the code clear?
- [ ] Add AI disclosure metadata to PR body (% AI-generated, tool used, human review applied)
- [ ] **SCREENSHOT:** PR comments showing C.L.E.A.R. review with AI disclosure
- **Points at risk:** ~8-10 pts in Claude Code Mastery

---

## Phase 4: MEDIUM — Team Process Documentation

### 4.1 Sprint documentation (2 sprints)
- [ ] Create `docs/sprints/sprint-1-planning.md` — goals, issues assigned, dates
- [ ] Create `docs/sprints/sprint-1-retro.md` — what went well, what didn't, action items
- [ ] Create `docs/sprints/sprint-2-planning.md`
- [ ] Create `docs/sprints/sprint-2-retro.md`
- **Points at risk:** ~6 pts in Team Process

### 4.2 Async standups (3+ per sprint per partner)
- [ ] Create `docs/standups/` directory
- [ ] Add standup entries (can be in GitHub Discussions, Slack exports, or markdown)
- [ ] Minimum 6 per partner across 2 sprints (3 per sprint)
- **Points at risk:** ~4 pts in Team Process

---

## Phase 5: REQUIRED — Deliverables (cannot skip any)

### 5.1 README.md with Mermaid architecture diagram
- [ ] Create root `README.md`
- [ ] Add project description, setup instructions
- [ ] Add Mermaid diagram showing: Frontend → Backend API → Services → DB/Redis, Agents pipeline (A→B→C→D)
- **Points at risk:** ~3 pts in Documentation

### 5.2 Technical blog post
- [ ] Write blog post on Medium or dev.to
- [ ] Cover: what FlowDay does, AI workflow insights, Claude Code features used, TDD with AI
- [ ] Publish and get URL
- **Points at risk:** ~4 pts in Documentation

### 5.3 Video demonstration (5-10 min)
- [ ] Record screen walkthrough showing:
  - App features (auth, projects, tasks, timer, weekly review)
  - Claude Code workflow (skills, hooks, TDD, MCP, agents)
  - CI/CD pipeline
- [ ] Keep between 5-10 minutes
- **Points at risk:** ~4 pts in Documentation

### 5.4 Individual reflections (500 words each)
- [ ] Each partner writes 500-word reflection
- [ ] Include specific Claude Code insights (what worked, what surprised you)
- **Points at risk:** ~2 pts in Documentation

### 5.5 Google Form showcase submission
- [ ] Submit: project name, URLs, thumbnail, video link, blog link
- [ ] Form URL: https://docs.google.com/forms/d/e/1FAIpQLScT67tnwjhIETSRwADt57TS_THJSeSGf-xrjTV2nmXvfFELg/viewform
- **Points at risk:** Required for submission

---

## Screenshots & Evidence Checklist

Capture these as you complete each task:

| # | Evidence | When to Capture | For |
|---|---|---|---|
| 1 | Skills usage (`/review-pr-v2` or `/tdd` in session) | During any PR | Claude Code Mastery |
| 2 | Skill v1→v2 (git log showing review-pr evolution) | Anytime | Claude Code Mastery |
| 3 | Hook firing (PreToolUse blocking bad commit msg) | During a commit | Claude Code Mastery |
| 4 | MCP tool call in session | After .mcp.json setup | Claude Code Mastery |
| 5 | Agent output (security-reviewer results) | After agent setup | Claude Code Mastery |
| 6 | `git worktree list` with 2+ worktrees | During parallel dev | Claude Code Mastery |
| 7 | C.L.E.A.R. PR review comment + AI disclosure | During PR review | Claude Code Mastery |
| 8 | App on public URL | After deployment | App Quality |
| 9 | CI pipeline all green | After CI fixes | CI/CD |
| 10 | Video demo recording | Last step | Documentation |

---

## What's Already Done (no action needed)

- [x] CLAUDE.md with @imports and git evolution
- [x] Auto-memory usage
- [x] 3 custom skills (review-pr, review-pr-v2, tdd-strict) with v1→v2 iteration
- [x] 2 hooks (PreToolUse commit validation + PostToolUse ruff reminder)
- [x] TDD red-green-refactor for 25 features (far exceeds 3 minimum)
- [x] Unit + integration tests (pytest + Vitest)
- [x] Property-based testing with hypothesis (bonus +3)
- [x] Mutation testing with mutmut (bonus +3)
- [x] Branch-per-issue workflow with PRs
- [x] GitHub Issues with acceptance criteria
- [x] AI attribution in commits (Co-Authored-By)
- [x] Lint (ruff) + type check (mypy) + tests + security scan (pip-audit) in CI
- [x] Docker build in CI

---

## Suggested Time Allocation

| Block | Tasks | Est. Time |
|---|---|---|
| Block 1 | Deploy (1.1) + .mcp.json (1.2) + agents (1.3) | 2-3 hours |
| Block 2 | Playwright E2E (2.1) + CI security gates (2.2-2.5) + OWASP (2.6) | 2-3 hours |
| Block 3 | Worktrees (3.1) + C.L.E.A.R. PRs (3.2) — capture screenshots | 1-2 hours |
| Block 4 | Sprint docs (4.1) + standups (4.2) | 1 hour |
| Block 5 | README (5.1) + blog (5.2) + reflections (5.4) | 2-3 hours |
| Block 6 | Video demo (5.3) + Google Form (5.5) | 1-2 hours |
| **Total** | | **~10-14 hours** |
