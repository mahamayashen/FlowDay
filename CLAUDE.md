# FlowDay — Claude Code Project Context

@import claude-project-instructions.md
@import docs/DATA_MODEL.md

## Tech Stack

- **Frontend:** React 18 + TypeScript 5 (Vite 5) — `frontend/`
- **Backend:** Python 3.12 + FastAPI — `backend/`
- **AI Orchestration:** Pydantic AI — `backend/agents/`
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic migrations
- **Cache/Queue:** Redis 7
- **Auth:** OAuth 2.0 (Google, GitHub) + JWT (access + refresh tokens)
- **Monitoring:** Grafana + Sentry + custom AI metrics
- **CI/CD:** Docker Compose (local), GitHub Actions (CI), Docker (prod)

## Architecture Decisions

### Monorepo structure
```
FlowDay/
├── frontend/          # React + TypeScript (Vite)
├── backend/           # Python + FastAPI
│   ├── api/           # Route handlers
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── agents/        # Pydantic AI agent definitions
│   ├── services/      # Business logic
│   ├── core/          # Config, security, deps
│   └── tests/         # pytest tests
├── docker/            # Dockerfiles, compose
├── .github/workflows/ # CI/CD pipelines
└── docs/              # Architecture docs, ADRs
```

### Backend patterns
- Async-first: all DB operations use SQLAlchemy async sessions via `asyncpg`
- Dependency injection via FastAPI's `Depends()` for services, DB sessions, auth
- Repository pattern: `models/` defines ORM, `services/` contains business logic — no raw queries in route handlers
- All API responses use Pydantic schemas from `schemas/`; never return ORM models directly

### AI agent architecture
- Multi-agent pipeline in `backend/agents/` — each agent is a standalone Pydantic AI `Agent` with its own `result_type` and `deps_type`
- Group A agents (Time, Meeting, Code, Task Analyst) run in parallel via `asyncio.gather`
- Group B (Pattern Detector) → Group C (Narrative Writer) → Group D (Judge) run sequentially
- Agent dependencies (DB, API clients) injected via Pydantic AI `RunContext` — never import directly
- Judge agent must use a different LLM provider than the Narrative Writer

### Frontend patterns
- Functional components + hooks only; no class components
- State: React Query for server state, Zustand for client state
- Dark theme: background `#111113`, warm accent colors — maintain consistently
- Component files: one component per file, co-locate styles and tests

## Coding Conventions

### Python (backend/)
- PEP 8 strictly enforced via `ruff`
- Type hints on all function signatures and return types
- Async functions where I/O is involved
- Docstrings on all public functions (Google style)
- Imports: stdlib → third-party → local, separated by blank lines
- Use `from __future__ import annotations` in all files
- Pydantic models: use `model_validator` over `validator` (v2 API)

### TypeScript (frontend/)
- Strict mode enabled in `tsconfig.json`
- Functional components with explicit return types
- Props interfaces named `{ComponentName}Props`
- No `any` — use `unknown` + type guards when type is uncertain
- Prefer `const` assertions and discriminated unions

### Git
- Branch: `feature/<issue-number>-short-description` or `fix/<issue-number>-short-description`
- Commit messages: imperative, descriptive (e.g., "add drag-and-drop to daily planner")
- PR → review → squash merge into `main`
- Never commit `.env`, secrets, or `node_modules/`

## Testing Strategy

### Backend
- Framework: `pytest` + `pytest-asyncio`
- Coverage target: 80%+ on `services/` and `agents/`
- Unit tests: mock external APIs and LLM calls; use Pydantic AI's `TestModel` for agent tests
- Integration tests: hit real PostgreSQL (Docker test container); never mock the database
- Agent tests: validate structured output schemas, test retry logic, test with `TestModel`
- Location: `backend/tests/` mirroring `backend/` structure

### Frontend
- Framework: Vitest + React Testing Library
- Unit tests for utility functions and hooks
- Component tests for user interactions (drag-drop, timer start/stop)
- No snapshot tests — they add noise, not confidence
- Location: co-located `*.test.tsx` files next to components

### CI pipeline order
lint → type-check → unit tests → integration tests → security scan → build

## Do's

- Always consider how a feature connects to the four production requirements (parallel agents, LLM-as-Judge, CI/CD+monitoring, security)
- Use Pydantic AI's `RunContext` and `deps_type` for agent dependency injection
- Use `asyncio.gather` for parallel agent execution — with proper error handling per agent
- Add Sentry breadcrumbs and Grafana metrics for any new API endpoint or agent run
- Use Alembic for all schema changes — never modify DB manually
- Encrypt OAuth tokens at rest using Fernet symmetric encryption
- Anonymize PII before passing user data to LLM agents
- Include `@import` references to relevant docs when creating sub-project CLAUDE.md files

## Don'ts

- Don't build V2 features (prescriptive AI, auto-scheduling, NLP chat, mobile) — flag scope creep
- Don't use class components in React
- Don't mock PostgreSQL in integration tests — use a real test database
- Don't return SQLAlchemy ORM objects from API endpoints — always serialize through Pydantic schemas
- Don't hardcode LLM provider — use Pydantic AI's provider-agnostic config
- Don't use the same LLM provider for both Narrative Writer and Judge agents
- Don't store secrets in code or commit `.env` files
- Don't skip type hints on Python functions or use `Any` in TypeScript
- Don't write raw SQL in route handlers — use the repository/service layer
