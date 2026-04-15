# Issue #8 — Add Sentry Error Tracking and Health Monitoring

## Phase 1: Explore

### What exists
- **Sentry**: `sentry-sdk[fastapi]` in deps; conditional init in `app/main.py:27-28` via `SENTRY_DSN`
- **Health**: `GET /health` returns `{"status": "ok"}` — no dependency checks (`app/api/health.py`)
- **Redis**: `REDIS_URL` in config, `redis>=5.0.0` in deps — **no connection code yet**
- **Database**: Async SQLAlchemy with `get_db()`, pool pre-ping enabled (`app/core/database.py`)
- **Auth**: `get_current_user()` dependency in `app/core/deps.py` — needed for gated endpoint
- **Tests**: `tests/test_health.py` has one test; `tests/conftest.py` has `db_engine` + `client` fixtures

### Impact analysis
- **No new pip deps** — `sentry-sdk[fastapi]` and `redis` already installed
- **No migrations** — no schema changes, only runtime health checks
- **Files to create**: `app/core/sentry.py`, `app/core/redis.py`, `tests/unit/test_sentry.py`, `tests/unit/test_redis.py`
- **Files to modify**: `app/main.py`, `app/api/health.py`, `app/schemas/health.py`, `tests/test_health.py`

---

## Phase 2: Plan

### Acceptance criteria
1. Sentry breadcrumb middleware logs request method + path on every request; missing `SENTRY_DSN` silently disables Sentry
2. Redis connection module provides `init_redis()` / `close_redis()` / `get_redis()` lifecycle
3. `GET /health` returns 200 with `database: "healthy"` + `redis: "healthy"` when both up; returns 503 when either is down
4. `GET /health/detailed` requires authentication and returns dependency latencies + Sentry status

---

### Cycle 1 — Sentry breadcrumb middleware

**RED tests** (`tests/unit/test_sentry.py`):
- `test_configure_sentry_with_dsn_calls_init` — mock `sentry_sdk.init`, verify it's called with DSN
- `test_configure_sentry_without_dsn_skips_init` — no DSN → `sentry_sdk.init` not called, no error
- `test_breadcrumb_middleware_adds_crumb` — mock `sentry_sdk.add_breadcrumb`, send request through middleware, verify breadcrumb added with method + path

**GREEN implementation**:
- Create `app/core/sentry.py`:
  - `configure_sentry(dsn: str | None)` — wraps `sentry_sdk.init` with guard
  - `SentryBreadcrumbMiddleware(BaseHTTPMiddleware)` — adds breadcrumb with `category="http"`, `message="{method} {path}"`, `level="info"` on each request
- Modify `app/main.py`:
  - Replace inline `sentry_sdk.init` with `configure_sentry(settings.SENTRY_DSN)`
  - Add `SentryBreadcrumbMiddleware` to app

**REFACTOR**:
- Remove direct `sentry_sdk` import from `main.py`

---

### Cycle 2 — Redis connection module

**RED tests** (`tests/unit/test_redis.py`):
- `test_get_redis_before_init_raises` — calling `get_redis()` before `init_redis()` raises `RuntimeError`
- `test_init_redis_creates_client` — after `init_redis()`, `get_redis()` returns a Redis client
- `test_close_redis_clears_client` — after `close_redis()`, `get_redis()` raises again

**GREEN implementation**:
- Create `app/core/redis.py`:
  - Module-level `_redis: Redis | None = None`
  - `init_redis(url: str) -> None` — creates `redis.asyncio.from_url(url)`
  - `close_redis() -> None` — calls `await _redis.aclose()`, sets to `None`
  - `get_redis() -> Redis` — returns client or raises `RuntimeError`
- Modify `app/main.py` lifespan:
  - Add `init_redis(settings.REDIS_URL)` at startup
  - Add `await close_redis()` at shutdown

**REFACTOR**:
- Ensure `redis.py` mirrors `database.py` module pattern (init/dispose/get)

---

### Cycle 3 — Enhanced `/health` with DB + Redis checks

**RED tests** (`tests/test_health.py`):
- `test_health_returns_ok_with_dependencies` — returns 200, body includes `status`, `database`, `redis` fields all "healthy"
- `test_health_returns_503_when_db_down` — mock DB to raise, returns 503, `database: "unhealthy"`
- `test_health_returns_503_when_redis_down` — mock Redis ping to raise, returns 503, `redis: "unhealthy"`

**GREEN implementation**:
- Modify `app/schemas/health.py`:
  - Add `database: str` and `redis: str` fields to `HealthResponse`
- Modify `app/api/health.py`:
  - Inject `db: AsyncSession = Depends(get_db)` and get Redis via `get_redis()`
  - Check DB: `await db.execute(text("SELECT 1"))`
  - Check Redis: `await redis.ping()`
  - Return 200 if both pass, 503 if either fails
  - Wrap each check in try/except to report individual status

**REFACTOR**:
- Extract health check logic into helper functions if needed

---

### Cycle 4 — Auth-gated `/health/detailed`

**RED tests** (`tests/test_health.py`):
- `test_health_detailed_requires_auth` — no token → 401
- `test_health_detailed_returns_dependency_info` — with valid auth, returns db latency, redis latency, sentry enabled flag, app version

**GREEN implementation**:
- Modify `app/schemas/health.py`:
  - Add `DetailedHealthResponse` with fields: `status`, `database` (dict with status + latency_ms), `redis` (dict with status + latency_ms), `sentry_enabled: bool`, `version: str`
- Modify `app/api/health.py`:
  - Add `GET /health/detailed` with `Depends(get_current_user)`
  - Measure DB + Redis latency with `time.monotonic()`
  - Return detailed response

**REFACTOR**:
- Clean up shared logic between `/health` and `/health/detailed`

---

### Post-implementation
- Run `ruff check . && ruff format .`
- Run `mypy .`
- Run `pytest -x -q`
- Run `mutmut run` — target ≥ 80% mutation score
- Open PR `feature/8-sentry-health-monitoring → main`, link Issue #8
