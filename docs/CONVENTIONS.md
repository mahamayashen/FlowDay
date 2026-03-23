# FlowDay — Coding Conventions & Testing

## Python (backend/)
- PEP 8 enforced via `ruff`
- Type hints on all function signatures and return types
- Async functions where I/O is involved
- Docstrings on all public functions (Google style)
- Imports: stdlib → third-party → local, separated by blank lines
- Use `from __future__ import annotations` in all files
- Pydantic models: use `model_validator` over `validator` (v2 API)

## TypeScript (frontend/)
- Strict mode enabled in `tsconfig.json`
- Functional components with explicit return types
- Props interfaces named `{ComponentName}Props`
- No `any` — use `unknown` + type guards when type is uncertain
- Prefer `const` assertions and discriminated unions

## Git
- Branch: `feature/<issue-number>-short-description` or `fix/<issue-number>-short-description`
- Commit messages: imperative, descriptive (e.g., "add drag-and-drop to daily planner")
- PR → review → squash merge into `main`
- Never commit `.env`, secrets, or `node_modules/`

## Testing — Backend
- Framework: `pytest` + `pytest-asyncio`
- Coverage target: 80%+ on `services/` and `agents/`
- Unit tests: mock external APIs and LLM calls; use Pydantic AI's `TestModel` for agent tests
- Integration tests: hit real PostgreSQL (Docker test container); never mock the database
- Agent tests: validate structured output schemas, test retry logic, test with `TestModel`
- Location: `backend/tests/` mirroring `backend/` structure

## Testing — Frontend
- Framework: Vitest + React Testing Library
- Unit tests for utility functions and hooks
- Component tests for user interactions (drag-drop, timer start/stop)
- No snapshot tests — they add noise, not confidence
- Location: co-located `*.test.tsx` files next to components

## CI pipeline order
lint → type-check → unit tests → integration tests → security scan → build
