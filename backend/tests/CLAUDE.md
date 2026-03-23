# FlowDay — Backend Tests Context

## Framework

- `pytest` + `pytest-asyncio`
- Coverage target: **80%+** on `services/` and `agents/`

## Rules

### Database
- **Never mock PostgreSQL** — integration tests must hit a real test DB (Docker container)
- Use a separate test database; never run tests against the dev or prod DB
- Fixtures should create and teardown data within the test transaction (roll back after each test)

### Agent tests
- Use Pydantic AI's `TestModel` to avoid real LLM calls in unit tests
- Validate structured output schemas — assert the shape of `result_type`, not just that it ran
- Test retry logic explicitly: simulate a Judge score < 80 and assert `ModelRetry` is raised
- Mock external API calls (Google Calendar, GitHub) with `pytest-mock`

### Structure
- Mirror `backend/app/` — e.g., tests for `app/services/task_service.py` live in `tests/services/test_task_service.py`
- Name test functions: `test_<what>_<expected_outcome>` (e.g., `test_create_task_returns_schema`)

### CI order
lint → type-check → unit tests → integration tests → security scan → build
