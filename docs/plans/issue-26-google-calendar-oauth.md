# Issue #26 — Google Calendar OAuth Integration

## Phase 1: Explore

### What exists
- `app/core/security.py` — `encrypt_oauth_token()` / `decrypt_oauth_token()` (Fernet, already used for login tokens)
- `app/api/auth.py` — Google OAuth login flow via raw `httpx`; `_handle_oauth_callback()` upserts user + stores encrypted token
- `app/services/sync_provider.py` — `BaseSyncProvider` ABC, `ProviderRegistry` singleton (`provider_registry`); no concrete providers yet
- `app/services/sync_service.py` — `trigger_sync()`, `get_sync_status()`
- `app/api/sync.py` — `GET /sync/status`, `POST /sync/{provider}/trigger`
- `app/models/external_sync.py` — table `external_syncs` with `sync_config_json` JSONB, `google_calendar` in provider enum
- `app/models/schedule_block.py` — `source` enum already includes `google_calendar`; `task_id` FK is non-nullable
- `app/core/config.py` — `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` already present
- Latest migration: `0007_add_external_syncs_table.py`

### Impact analysis
- **No Alembic migration** — reusing `sync_config_json` JSONB for encrypted token storage
- **No new pip dependencies** — raw `httpx` (already present) for all Google API calls
- ScheduleBlock requires a `Task → Project → User` chain; sync provider must manage a sentinel "Google Calendar" project per user
- 6 new files (3 source, 3 test), 5 modified files

---

## Phase 2: Plan

### Acceptance criteria
1. `GET /sync/google-calendar/auth` initiates Google OAuth consent flow and returns an authorization URL
2. `GET /sync/google-calendar/callback` exchanges the auth code, stores encrypted tokens in `external_syncs.sync_config_json`, and returns the sync record
3. Calendar sync service fetches events from the Google Calendar API and handles token refresh for expired tokens
4. `GoogleCalendarSyncProvider` syncs events as `ScheduleBlock` rows with `source="google_calendar"`, registered with the provider registry

---

### Cycle 1 — OAuth flow endpoints

**RED tests** (`tests/unit/test_google_calendar_routes.py`):
- `test_auth_returns_authorization_url` — GET `/sync/google-calendar/auth` returns 200 with `{"authorization_url": "https://accounts.google.com/..."}` containing calendar scope
- `test_auth_requires_authentication` — unauthenticated request returns 401
- `test_callback_success_creates_sync_record` — GET `/sync/google-calendar/callback?code=xxx&state=<user_id>` with mocked Google token exchange → 200, returns `SyncStatusResponse`
- `test_callback_rejects_invalid_state` — mismatched state → 400
- `test_callback_requires_authentication` — unauthenticated request returns 401

**GREEN implementation**:
- `app/core/config.py` — add `GOOGLE_CALENDAR_REDIRECT_URI: str = "http://localhost:5060/sync/google-calendar/callback"`
- `app/schemas/sync.py` — add `GoogleCalendarAuthResponse(BaseModel)` with `authorization_url: str`
- `app/services/google_calendar.py` — create with:
  - `GOOGLE_CALENDAR_SCOPE`, `GOOGLE_AUTH_URL`, `GOOGLE_TOKEN_URL`, `GOOGLE_CALENDAR_EVENTS_URL` constants
  - `build_authorization_url(user_id: str) -> str` — builds consent URL with `access_type=offline`, `prompt=consent`, `state=user_id`
  - `async exchange_code_for_tokens(code: str) -> dict` — POST to Google token endpoint, returns token dict
  - `async store_tokens_in_sync_record(db, sync_record, token_data) -> None` — encrypts + stores in `sync_config_json`
- `app/api/sync.py` — add two route handlers:
  - `GET /google-calendar/auth` — calls `build_authorization_url(str(current_user.id))`
  - `GET /google-calendar/callback` — calls `exchange_code_for_tokens()`, upserts `ExternalSync` row, calls `store_tokens_in_sync_record()`
- `backend/.env.example` — add `GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5060/sync/google-calendar/callback`

**REFACTOR**:
- Extract Google token endpoint POST into a shared private helper to avoid duplication with Cycle 3's refresh logic

---

### Cycle 2 — Calendar sync service (event fetching + token refresh)

**RED tests** (`tests/unit/test_google_calendar_service.py`):
- `test_build_authorization_url_contains_scope_and_state` — URL has `calendar.readonly`, `access_type=offline`, `state`
- `test_exchange_code_success_returns_tokens` — mock httpx POST, returns access + refresh tokens
- `test_exchange_code_failure_raises_http_exception` — Google returns 400 → HTTPException 401
- `test_refresh_access_token_success` — mock httpx POST, returns new access token
- `test_refresh_keeps_old_refresh_token_when_omitted` — Google omits refresh_token → old one preserved
- `test_refresh_failure_raises_http_exception` — Google returns error → HTTPException 401
- `test_fetch_calendar_events_returns_list` — mock httpx GET, returns list of event dicts
- `test_fetch_calendar_events_handles_pagination` — mock two pages (`nextPageToken`)
- `test_store_tokens_encrypts_before_storage` — verifies `encrypt_oauth_token` called, JSON keys set
- `test_get_valid_token_returns_cached_when_not_expired` — no refresh call made
- `test_get_valid_token_refreshes_when_expired` — calls `refresh_access_token()`, stores updated tokens

**GREEN implementation**:
- `app/services/google_calendar.py` — complete implementation of:
  - `async refresh_access_token(encrypted_refresh_token: str) -> dict`
  - `async fetch_calendar_events(access_token: str, time_min: str, time_max: str) -> list[dict]` — paginates automatically
  - `async get_valid_access_token(db, sync_record) -> str` — checks expiry, refreshes if needed

**REFACTOR**:
- Consolidate duplicate httpx call patterns into `_post_to_token_endpoint(payload: dict) -> dict`

---

### Cycle 3 — Sync provider + integration

**RED tests**:

`tests/unit/test_google_calendar_provider.py`:
- `test_provider_registered_in_registry` — after import, `provider_registry.get("google_calendar")` is `GoogleCalendarSyncProvider`
- `test_sync_creates_sentinel_project_and_task_and_block` — mock `get_valid_access_token` + `fetch_calendar_events`, verify `ScheduleBlock` rows created with `source="google_calendar"`
- `test_sync_deletes_old_google_calendar_blocks_before_inserting` — existing blocks removed before new ones added
- `test_sync_skips_all_day_events` — events with `start.date` (no `start.dateTime`) are ignored
- `test_sync_handles_token_error_propagates` — token error propagates to sync framework

`tests/integration/test_google_calendar_sync.py`:
- `test_callback_creates_external_sync_record` — mocked Google token exchange, real DB, verifies `external_syncs` row with encrypted tokens
- `test_sync_trigger_creates_schedule_blocks` — pre-inserted `ExternalSync` with tokens, mocked calendar API, `POST /sync/google_calendar/trigger` → `ScheduleBlock` rows in DB

**GREEN implementation**:
- `app/services/google_calendar_provider.py` — `GoogleCalendarSyncProvider(BaseSyncProvider)`:
  - `async sync(db, sync_record)`:
    1. Call `get_valid_access_token()`
    2. Fetch events for today → today+7 days
    3. Get or create sentinel `Project` (`name="Google Calendar"`, `color="#4285F4"`) for user
    4. Delete existing `ScheduleBlock` rows with `source="google_calendar"` for user in date range (via join through Task→Project)
    5. For each event with `start.dateTime`: create `Task` + `ScheduleBlock`
  - Module-level: `provider_registry.register("google_calendar", GoogleCalendarSyncProvider)`
- `app/main.py` — add `import app.services.google_calendar_provider  # noqa: F401` in `create_app()`

**REFACTOR**:
- Extract `_get_or_create_sentinel_project()` helper
- Extract `_event_to_schedule_block()` pure function for testability
- Ensure timezone handling is correct (convert Google's ISO 8601 with tz offset to date + decimal hours)

---

### Post-implementation
- Run `ruff check . && ruff format .`
- Run `mypy .`
- Run `mutmut run --paths-to-mutate=app/services/google_calendar.py,app/services/google_calendar_provider.py`
- Target: ≥ 80% mutation score
- Open PR `feature/26-google-calendar-oauth → main`, link Issue #26
