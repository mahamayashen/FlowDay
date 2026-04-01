# Issue #3 — Implement User Model and OAuth 2.0 + JWT Auth

## Phase 1: Explore

### What exists
- `app/core/config.py` — `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` (15), `REFRESH_TOKEN_EXPIRE_DAYS` (7) already defined
- `app/core/database.py` — Async engine + `get_db()` dependency working
- `app/models/base.py` — `DeclarativeBase` ready for model inheritance
- `alembic/env.py` — Async migration runner, imports `Base.metadata`
- `alembic/versions/0001_initial.py` — Empty baseline migration
- `pyproject.toml` — `python-jose[cryptography]`, `cryptography` already in deps
- No user model, schemas, security module, deps, or auth routes exist yet

### Impact analysis
- **New files:** `models/user.py`, `schemas/user.py`, `core/security.py`, `core/deps.py`, `api/auth.py`
- **Modified files:** `main.py` (register auth router), `models/__init__.py` (export User for Alembic)
- **Database:** New `users` table with UUID PK, Alembic migration `0002_add_users`
- **Security:** Fernet encryption for OAuth tokens, JWT access+refresh tokens
- **No blockers:** All pip dependencies already present

---

## Phase 2: Plan

### Acceptance criteria
1. Fernet encryption can encrypt and decrypt OAuth tokens; JWT access and refresh tokens can be created and decoded
2. User SQLAlchemy model exists with correct columns, constraints, and Alembic migration applies cleanly
3. Pydantic User schemas serialize User model without exposing raw OAuth tokens
4. `get_current_user` dependency validates JWT and rejects expired/invalid tokens with 401

---

### Cycle 1 — Security utilities (Fernet + JWT)

**RED tests** (`tests/unit/test_security.py`):
- `test_encrypt_token_returns_different_string` — encrypted != plaintext
- `test_decrypt_token_returns_original` — roundtrip encrypt/decrypt
- `test_encrypt_empty_string_raises` — ValueError on empty input
- `test_create_access_token_returns_string` — JWT string returned
- `test_decode_access_token_returns_subject` — decode roundtrip, `sub` matches
- `test_decode_expired_token_raises` — expired token raises `JWTError`
- `test_create_refresh_token_has_longer_expiry` — refresh exp > access exp
- `test_fernet_roundtrip_with_random_input` — `@given(st.text(min_size=1, max_size=500))` hypothesis property test

**GREEN implementation** (`app/core/security.py`):
- `encrypt_oauth_token(plain: str) -> str` — Fernet encrypt using `SECRET_KEY`
- `decrypt_oauth_token(encrypted: str) -> str` — Fernet decrypt
- `create_access_token(subject: str, extra: dict | None) -> str` — JWT with `exp` = now + 15 min
- `create_refresh_token(subject: str) -> str` — JWT with `exp` = now + 7 days
- `decode_token(token: str) -> dict` — decode and validate, raise on expired/invalid

**REFACTOR:**
- Extract Fernet key derivation into a cached helper `_get_fernet()` so the key isn't re-derived on every call

---

### Cycle 2 — User model + Alembic migration

**RED tests** (`tests/unit/test_user_model.py`):
- `test_user_model_has_required_columns` — inspect `User.__table__.columns` for: id, email, name, hashed_password, google_oauth_token, github_oauth_token, settings_json, created_at, updated_at
- `test_user_id_is_uuid` — column type is UUID
- `test_user_email_is_unique` — unique constraint exists
- `test_user_settings_json_defaults_to_empty` — server_default is `{}`

**RED tests** (`tests/integration/test_user_migration.py`):
- `test_alembic_upgrade_creates_users_table` — after `alembic upgrade head`, `users` table exists in DB

**GREEN implementation:**
- `app/models/user.py` — SQLAlchemy `User(Base)` with all columns per DATA_MODEL.md
- `app/models/__init__.py` — export `User` so Alembic autogenerate sees it
- `alembic revision --autogenerate -m "add users table"` → `0002_add_users.py`

**REFACTOR:**
- Add `__repr__` to User model for debugging
- Ensure `updated_at` uses `onupdate=func.now()`

---

### Cycle 3 — User Pydantic schemas

**RED tests** (`tests/unit/test_user_schema.py`):
- `test_user_response_excludes_oauth_tokens` — `UserResponse` schema has no `google_oauth_token` or `github_oauth_token` fields
- `test_user_response_from_orm` — can create `UserResponse` from a User-like object via `model_validate`
- `test_user_response_includes_id_email_name` — required fields present
- `test_user_create_schema_validates_email` — invalid email raises `ValidationError`

**GREEN implementation** (`app/schemas/user.py`):
- `UserResponse` — id, email, name, settings_json, created_at (no token fields)
- `UserCreate` — email, name, password (optional, for future local auth)
- `TokenResponse` — access_token, refresh_token, token_type

**REFACTOR:**
- Move `HealthResponse` from `api/health.py` into `schemas/health.py` for consistency (all schemas in `schemas/`)

---

### Cycle 4 — `get_current_user` dependency + auth routes

**RED tests** (`tests/unit/test_deps.py`):
- `test_get_current_user_returns_user_for_valid_token` — given valid JWT with user email as `sub`, returns User
- `test_get_current_user_raises_401_for_expired_token` — expired JWT → HTTPException 401
- `test_get_current_user_raises_401_for_invalid_token` — garbage string → 401
- `test_get_current_user_raises_401_for_missing_sub` — JWT without `sub` claim → 401
- `test_get_current_user_raises_401_for_nonexistent_user` — valid JWT but user not in DB → 401

**RED tests** (`tests/integration/test_auth.py`):
- `test_auth_google_callback_creates_user_and_returns_jwt` — mock Google OAuth response, verify user created + JWT returned
- `test_auth_github_callback_creates_user_and_returns_jwt` — mock GitHub OAuth response, verify same
- `test_auth_callback_existing_user_updates_token` — second OAuth login updates encrypted token, doesn't duplicate user
- `test_refresh_token_returns_new_access_token` — POST /auth/refresh with valid refresh token → new access token
- `test_refresh_with_invalid_token_returns_401` — bad refresh token → 401

**GREEN implementation:**
- `app/core/deps.py` — `get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User`
- `app/api/auth.py` — routes:
  - `GET /auth/google/callback` — exchange code for token, create/update user, return JWT
  - `GET /auth/github/callback` — same flow for GitHub
  - `POST /auth/refresh` — validate refresh token, issue new access token
  - `GET /auth/me` — return current user (uses `get_current_user`)
- `app/main.py` — register `auth_router`

**REFACTOR:**
- Extract OAuth provider logic into a helper `_handle_oauth_callback(provider, code, db)` to DRY Google/GitHub flows
- Add Sentry breadcrumbs for auth events

---

### Post-implementation
- Run `ruff check . && ruff format .` — fix any lint issues
- Run `mutmut run --paths-to-mutate=app/core/security.py` — target ≥ 80% mutation score
- Run `mutmut run --paths-to-mutate=app/core/deps.py` — target ≥ 80% mutation score
- Open PR: `feature/3-user-auth → main`, link Issue #3
