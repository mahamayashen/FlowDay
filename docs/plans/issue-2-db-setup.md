# Issue #2 — PostgreSQL + SQLAlchemy Async + Alembic Setup

## Phase 1: Explore

### What exists
- `backend/app/core/config.py` — Pydantic Settings with `DATABASE_URL` defaulting to `postgresql+asyncpg://flowday:flowday@localhost:5432/flowday`
- `backend/app/main.py` — FastAPI app factory, no lifespan context yet
- `backend/pyproject.toml` — `sqlalchemy[asyncio]`, `asyncpg`, `alembic` already declared as dependencies
- `backend/tests/conftest.py` — async HTTP client fixture, no DB fixtures
- No `alembic/` directory, no `app/models/`, no `app/core/database.py`

### Impact analysis
- Adding Alembic requires: `alembic.ini`, `alembic/env.py`, `alembic/versions/`
- Async engine needs a `Base` metadata to attach to — requires `app/models/base.py`
- `get_db()` dependency must be available before any route handler that touches the DB
- Engine lifecycle should be tied to FastAPI startup/shutdown (lifespan), not module-level globals
- Integration tests require real PostgreSQL — Docker Compose needed locally

### Missing dev dependencies
- `hypothesis` — property-based testing
- `mutmut<3` — mutation testing (v3 skips committed files)
- `pytest-cov` — coverage reporting

---

## Phase 2: Plan

### Acceptance criteria
1. `alembic upgrade head` completes without errors
2. `AsyncSession` is injectable via `Depends(get_db)` in route handlers

### Cycle 1 — Alembic initializes and migrates cleanly

**RED tests** (`tests/integration/test_db_migrations.py`):
- `test_alembic_upgrade_head_runs_without_error` — subprocess, assert exit code 0
- `test_alembic_current_returns_a_revision_after_upgrade` — assert `"(head)"` in output

**GREEN implementation**:
- `alembic.ini` — `script_location = alembic`, `prepend_sys_path = .`
- `alembic/env.py` — async engine via `run_async_migrations`, reads `DATABASE_URL` env var
- `alembic/versions/0001_initial.py` — empty baseline migration
- `app/models/base.py` — `Base = DeclarativeBase()`

**REFACTOR**:
- `alembic/env.py` — replace `os.environ.get` with `settings.DATABASE_URL` (single source of truth)

### Cycle 2 — AsyncSession injectable via `Depends(get_db)`

**RED tests** (`tests/integration/test_db_session.py`):
- `test_get_db_yields_async_session` — assert yielded value is `AsyncSession`
- `test_session_can_execute_select_1` — assert `SELECT 1` returns 1
- `test_create_async_engine_accepts_valid_asyncpg_url` — `@given` hypothesis property test, 50 random (host, port, dbname) combinations

**GREEN implementation**:
- `app/core/database.py` — `init_engine()`, `dispose_engine()`, `get_db()`

**REFACTOR**:
- Move engine creation into FastAPI `lifespan` context manager in `main.py`
- Dispose engine cleanly on shutdown

### Post-implementation
- Run `mutmut run` on `app/core/database.py`
- Target: ≥ 80% mutation score
- Open PR `feature/2-db-setup → main`, link Issue #2

---

## Phase 3: Implement

See commit history on `feature/2-db-setup`:
- `[#2][RED]` → `[#2][GREEN]` → `[#2][REFACTOR]` × 2 cycles

## Phase 4: Commit / Result

- **14 tests** passing (unit + integration)
- **85% mutation score** (11/13) on `app/core/database.py`
- `ruff` + `mypy --strict` clean
- CI green on GitHub Actions (Postgres 16 service container)
