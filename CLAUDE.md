# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# FlowDay — Claude Code Project Context

@import claude-project-instructions.md
@import docs/DATA_MODEL.md
@import docs/CONVENTIONS.md

## Tech Stack

- **Frontend:** React 18 + TypeScript 5 (Vite 5) — `frontend/`
- **Backend:** Python 3.12 + FastAPI — `backend/`
- **AI Orchestration:** Pydantic AI — `backend/agents/`
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic migrations
- **Cache/Queue:** Redis 7
- **Auth:** OAuth 2.0 (Google, GitHub) + JWT (access + refresh tokens)
- **Monitoring:** Grafana + Sentry + custom AI metrics
- **CI/CD:** Docker Compose (local), GitHub Actions (CI), Docker (prod)

## Build & Run Commands

### Environment setup
```
conda activate vibing   # Python 3.12 — must be active before any backend commands
```

### Backend (from `backend/`)
```
uvicorn app.main:app --reload --port 5060    # Start dev server (port 5060)
pytest                                        # Run all tests
pytest -x -q                                  # Stop on first failure
pytest tests/path/to/test_file.py::test_name  # Run a single test
ruff check . && ruff format .                 # Lint + format
mypy .                                        # Type check
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "description"  # New migration
mutmut run                                    # Mutation testing (target ≥ 80% score)
mutmut results                                # View mutation results
```

### Frontend (from `frontend/`)
```
npm run dev       # Vite dev server
npm run build     # Production build
npm run lint      # ESLint
npx vitest        # Run tests
```

### Infrastructure
```
docker compose -f docker/docker-compose.yml up -d     # Start PostgreSQL + Redis
docker compose -f docker/docker-compose.yml down       # Stop services
docker compose -f docker/docker-compose.test.yml up -d # Start isolated test DB (port 5433)
docker build -t flowday-backend backend/               # Build production image
```

## Architecture — Key Decisions

- Async-first backend: SQLAlchemy async sessions via `asyncpg`, FastAPI `Depends()` for DI
- Repository pattern: `services/` owns business logic, `schemas/` for all API responses — never return ORM models
- AI pipeline in `backend/agents/`: Group A (Time, Meeting, Code, Task) run parallel via `asyncio.gather` → Group B (Pattern Detector) → Group C (Narrative Writer) → Group D (Judge)
- Agent deps injected via Pydantic AI `RunContext` — never import directly
- Judge agent must use a different LLM provider than Narrative Writer
- Frontend: functional components + hooks only, React Query + Zustand, dark theme (`#111113`)

## Development Workflow (required for every issue)

### 4-Phase Workflow — never skip phases

Every issue MUST follow these 4 phases in order. Use the custom slash commands to enforce each phase:

#### Phase 1: Explore (`/explore-issue`)
- Read existing code and understand impact — **no file changes allowed**
- Identify affected files, dependencies, missing dev dependencies
- Document what exists vs. what's needed
- Use plan mode (`EnterPlanMode`) to explore without accidental edits
- Output: understanding of scope and impact

#### Phase 2: Plan (`/plan-issue`)
- Write implementation plan to `docs/plans/issue-<N>-<name>.md`
- Define acceptance criteria (one per TDD cycle)
- Specify RED tests, GREEN implementation, REFACTOR cleanup for each cycle
- Get user confirmation before proceeding to implement
- Output: approved plan document

#### Phase 3: Implement (`/tdd`)
- Strict AI-TDD cycles — one cycle per acceptance criterion
- **RED** — write failing test first, run it to confirm failure, commit: `[#N][RED] add failing test: <description>`
- **GREEN** — write minimum code to pass, run tests, commit: `[#N][GREEN] implement: <description>`
- **REFACTOR** — clean up without breaking tests, run tests, commit: `[#N][REFACTOR] refactor: <description>`
- After all cycles: run `ruff check . && ruff format .`, then `mutmut run` (target ≥ 80%)
- Property-based testing (`hypothesis`) — use `@given` for core logic

#### Phase 4: Commit
- Feature branch only — never commit directly to `main`
- Branch naming: `feature/<issue-number>-short-description`
- Open PR: `feature/<N>-<name> → main`, link Issue #N
- All commits use `[#N][RED|GREEN|REFACTOR]` prefix format

### Context Management

- `/compact` — compress context mid-task when token usage is high
- `/context` — check token consumption breakdown
- `claude --continue` — resume previous session after terminal close
- `/clear` — reset between unrelated tasks or features
- One feature per session — `/clear` between different features

## Do's

- Connect every feature to the four production requirements (parallel agents, LLM-as-Judge, CI/CD+monitoring, security)
- Use `asyncio.gather` for parallel agents — with per-agent error handling
- Use Alembic for all schema changes
- Encrypt OAuth tokens at rest (Fernet); anonymize PII before LLM calls
- Add Sentry breadcrumbs and Grafana metrics for new endpoints/agent runs
- Always run tests before committing — the pre-commit hook enforces commit message format
- Use `/explore-issue` before touching any code for a new issue
- Use `/tdd` to enforce strict RED/GREEN/REFACTOR discipline

## Don'ts

- Don't build V2 features (prescriptive AI, auto-scheduling, NLP chat, mobile) — flag scope creep
- Don't mock PostgreSQL in integration tests — use real test DB
- Don't hardcode LLM provider — use Pydantic AI's provider-agnostic config
- Don't store secrets in code or commit `.env`
- Don't write raw SQL in route handlers — use service layer
- Don't skip TDD phases — no writing implementation before a failing test exists
- Don't commit without the `[#N][RED|GREEN|REFACTOR]` prefix
- Don't skip the Explore phase — understand before you build
