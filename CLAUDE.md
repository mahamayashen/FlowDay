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

### Backend (from `backend/`)
```
uvicorn app.main:app --reload    # Start dev server
pytest                           # Run all tests
pytest -x -q                     # Stop on first failure
ruff check . && ruff format .    # Lint + format
mypy .                           # Type check
alembic upgrade head             # Apply migrations
alembic revision --autogenerate -m "description"  # New migration
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
docker compose up -d    # Start PostgreSQL + Redis
docker compose down     # Stop services
```

## Architecture — Key Decisions

- Async-first backend: SQLAlchemy async sessions via `asyncpg`, FastAPI `Depends()` for DI
- Repository pattern: `services/` owns business logic, `schemas/` for all API responses — never return ORM models
- AI pipeline in `backend/agents/`: Group A (Time, Meeting, Code, Task) run parallel via `asyncio.gather` → Group B (Pattern Detector) → Group C (Narrative Writer) → Group D (Judge)
- Agent deps injected via Pydantic AI `RunContext` — never import directly
- Judge agent must use a different LLM provider than Narrative Writer
- Frontend: functional components + hooks only, React Query + Zustand, dark theme (`#111113`)

## Do's

- Connect every feature to the four production requirements (parallel agents, LLM-as-Judge, CI/CD+monitoring, security)
- Use `asyncio.gather` for parallel agents — with per-agent error handling
- Use Alembic for all schema changes
- Encrypt OAuth tokens at rest (Fernet); anonymize PII before LLM calls
- Add Sentry breadcrumbs and Grafana metrics for new endpoints/agent runs

## Don'ts

- Don't build V2 features (prescriptive AI, auto-scheduling, NLP chat, mobile) — flag scope creep
- Don't mock PostgreSQL in integration tests — use real test DB
- Don't hardcode LLM provider — use Pydantic AI's provider-agnostic config
- Don't store secrets in code or commit `.env`
- Don't write raw SQL in route handlers — use service layer
