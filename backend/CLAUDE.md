# FlowDay — Backend Context

@import ../docs/CONVENTIONS.md

## Layout

```
backend/
├── app/
│   ├── main.py          # FastAPI app factory
│   ├── api/             # Route handlers (thin — delegate to services)
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── agents/          # Pydantic AI agent definitions
│   ├── services/        # Business logic
│   └── core/            # Config, security, deps (DB session, auth)
└── tests/               # pytest suite — see tests/CLAUDE.md
```

## Patterns

- All DB operations are async (`AsyncSession` via `asyncpg`); inject session with `Depends(get_db)`
- Route handlers must stay thin: validate input → call service → return schema
- Never return SQLAlchemy ORM objects from endpoints — always serialize through Pydantic schemas in `schemas/`
- Services own business logic; models own DB structure; schemas own API contracts

## Agent Pipeline (`app/agents/`)

Groups and execution order:
- **Group A (parallel):** `time_analyst`, `meeting_analyst`, `code_analyst`, `task_analyst` — run via `asyncio.gather` with per-agent error handling
- **Group B → C → D (sequential):** `pattern_detector` → `narrative_writer` → `judge`

Rules:
- Each agent has its own `result_type` and `deps_type`
- Inject all dependencies (DB, API clients) via Pydantic AI `RunContext` — never import directly inside agents
- Judge agent must use a **different** LLM provider than Narrative Writer
- Judge score < 80 triggers `ModelRetry`; max 2 retries

## Key Commands (run from `backend/`)

```bash
uvicorn app.main:app --reload          # Dev server
alembic upgrade head                   # Apply migrations
alembic revision --autogenerate -m ""  # New migration
ruff check . && ruff format .          # Lint + format
mypy .                                 # Type check
```
