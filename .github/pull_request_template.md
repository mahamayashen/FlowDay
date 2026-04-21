<!--
Thanks for opening a PR! Fill each section before requesting review.
Every PR in FlowDay is reviewed against the C.L.E.A.R. framework — use the
checklist to self-review before handing off.
-->

## Summary

<!-- 1–3 bullets: what changed and why. Link the issue. -->
- Closes #
-

## C.L.E.A.R. Self-Review

### Context — why does this change exist?
- [ ] Linked to an issue with clear acceptance criteria
- [ ] PR description explains the *why*, not just the *what*
- [ ] Scope matches the issue (no silent scope creep)

### Logic — is the implementation correct?
- [ ] Happy path covered
- [ ] Edge cases considered (empty input, concurrent writes, upstream failure, timezone, pagination, …)
- [ ] Async / transactional semantics sound (no unawaited coroutines, no partial commits)

### Evidence — how do we know it works?
- [ ] Unit tests added / updated
- [ ] Integration tests hit real dependencies (Postgres, Redis) — no mocked DB
- [ ] `pytest` green locally
- [ ] `ruff check .` and `ruff format --check .` clean
- [ ] `mypy .` clean
- [ ] `mutmut run` ≥ 80% (for changes to `services/` or `agents/`)
- [ ] Manual verification or screenshot attached for UI / API changes

### Architecture — does it fit the codebase?
- [ ] Route handlers stay thin (validate → service → schema)
- [ ] No raw SQL in routes; all DB access via service layer
- [ ] Pydantic schemas used for every API boundary (no ORM models returned)
- [ ] Agent dependencies injected via `RunContext`, not imported directly
- [ ] Naming / path conventions consistent with surrounding code

### Risk — what could go wrong?
- [ ] Alembic migration is reversible (downgrade tested, or explicitly note why not)
- [ ] User-scoping enforced — no cross-user data leaks (return 404, not 403, for foreign ids)
- [ ] Secrets / OAuth tokens encrypted at rest; no PII sent to LLMs unsanitised
- [ ] Sentry breadcrumbs added for new endpoints and agent pipeline stages
- [ ] Known limitations / follow-ups captured as issues

## Test Plan

<!-- Concrete commands + what passing looks like. -->
- [ ]
- [ ]

## Follow-ups

<!-- Anything deliberately out of scope, linked to a tracking issue. -->
-
