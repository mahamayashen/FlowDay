# Definition of Done — FlowDay

A change is "done" only when **every** checkbox below is satisfied. This applies to
every Issue, Pull Request, and feature branch before merge into `main`.

Scope reminder: this project targets at minimum **4 of the 8 security gates** and
integrates them across pre-commit, CI, and human review (see CLAUDE.md §Security
and `.github/workflows/ci.yml` stage 5).

---

## 1. Functional

- [ ] All acceptance criteria from the plan in `docs/plans/issue-<N>-<name>.md` are met
- [ ] Feature works end-to-end on a developer machine (manual smoke test documented in PR)
- [ ] Edge cases listed in the plan are covered by tests
- [ ] No V2 features smuggled in (prescriptive AI, auto-scheduling, NLP chat, mobile)

## 2. Code Quality

- [ ] `ruff check . && ruff format .` passes (backend)
- [ ] `mypy .` passes with `strict = true` (backend)
- [ ] `npm run lint` passes with `--max-warnings 0` (frontend)
- [ ] `npx tsc --noEmit` passes (frontend)
- [ ] No raw SQL in route handlers — business logic lives in `services/`
- [ ] ORM models are **never** returned from endpoints — always via Pydantic schemas

## 3. Testing (TDD)

- [ ] Each acceptance criterion has a RED → GREEN → REFACTOR commit trail
- [ ] Commits use the `[#N][RED|GREEN|REFACTOR]` prefix
- [ ] `pytest` passes (unit + integration); integration tests hit the real test DB
- [ ] `npx vitest` passes; Playwright E2E passes if UI changed
- [ ] `mutmut run` mutation score ≥ 80% on touched modules
- [ ] Property-based tests (`hypothesis`) added for any core logic

## 4. Security — MUST-PASS Gates

The PR cannot be merged unless **all four primary gates** below are green in CI.
CI fails closed: any gate failure blocks merge.

### Gate 1 — Secrets Detection (Gitleaks) — REQUIRED
- [ ] Gitleaks pre-commit hook ran locally (no bypass with `--no-verify`)
- [ ] Gitleaks job in CI is green
- [ ] No `.env`, `*.pem`, `credentials.json`, or API keys in the diff
- [ ] Any newly introduced secret lives in GitHub Actions secrets / Vercel env, not code

### Gate 2 — Dependency Scanning — REQUIRED
- [ ] `pip-audit` passes (no high/critical Python CVEs)
- [ ] `npm audit --audit-level=high` passes (no high/critical Node CVEs)
- [ ] Any new dependency is pinned (`>=X.Y.Z` with known-safe floor)
- [ ] Transitive vulnerabilities have a documented suppression with rationale and
      upstream tracking link (comment in `pyproject.toml` or `package.json`)

### Gate 3 — SAST (Bandit) — REQUIRED
- [ ] Bandit runs clean with `backend/bandit.yml` config
- [ ] Any Bandit suppression (`# nosec BXXX`) has an inline rationale
- [ ] No `eval`, `exec`, `pickle.load` on untrusted input
- [ ] No `subprocess` with `shell=True` on user-controlled args
- [ ] No `yaml.load` without `Loader=yaml.SafeLoader`

### Gate 7 — Security Acceptance Criteria — REQUIRED
Every change that touches auth, data persistence, external APIs, or LLM prompts
must answer each of the following in the PR description:

- [ ] **A01 Access Control:** every new endpoint declares a `Depends()` auth guard
      and a role/ownership check in the service layer
- [ ] **A02 Cryptography:** any new secret value is encrypted at rest (Fernet) and
      transmitted over TLS; nothing sensitive is logged
- [ ] **A03 Injection:** all new DB queries use SQLAlchemy parameters (no string
      interpolation); all new API inputs are Pydantic-validated; any new LLM
      prompt anonymizes PII before the call
- [ ] **A04 Insecure Design:** Judge agent still uses a different LLM provider
      than Narrative Writer; no business logic leaked into routes
- [ ] **A05 Misconfiguration:** CORS allowlist unchanged or reviewed; Docker
      container still runs non-root; no debug flags in prod code paths
- [ ] **A07 Auth Failures:** no custom password storage introduced; JWT lifetimes
      unchanged or justified; refresh rotation still works
- [ ] **A09 Logging:** Sentry breadcrumbs added for the new code path; no PII
      sent to Sentry; audit log written for auth-relevant events
- [ ] **A10 SSRF:** any new external URL is on the allowlist, not user-supplied

## 5. Observability

- [ ] New endpoints have Prometheus metrics (latency + error rate)
- [ ] New agent runs emit the standard judge-score / duration metrics
- [ ] Grafana dashboard updated if a new metric was added
- [ ] Sentry captures exceptions with user context (no PII)

## 6. Documentation

- [ ] CLAUDE.md still reflects reality (update if architecture changed)
- [ ] `docs/plans/issue-<N>-*.md` marked as implemented and linked from the PR
- [ ] Breaking changes documented in the PR description with migration notes
- [ ] Alembic migration committed for any schema change

## 7. CI / Merge

- [ ] All required CI stages green: `backend-quality`, `frontend-quality`,
      `backend-tests`, `frontend-tests`, `e2e-tests`, `security-gates`
- [ ] Branch rebased on latest `main` (no merge commits)
- [ ] PR reviewed by ≥ 1 human (AI review via `ai-review` label is supplementary,
      not a substitute)
- [ ] Squash-merged into `main` with the issue number in the subject

---

## 8-Gate Taxonomy — Coverage Map

This project implements **4 of 8** gates today. The remaining four are on the
roadmap (marked `[planned]`) and not required for merge.

| Gate | Name | Tool | Where it runs |
|---|---|---|---|
| 1 | Secrets Detection | Gitleaks | pre-commit + CI `security-gates` |
| 2 | Dependency Scanning | pip-audit + npm audit | CI `security-gates` |
| 3 | SAST (Static) | Bandit | pre-commit + CI `security-gates` |
| 4 | DAST (Dynamic) | *(planned — ZAP baseline on preview URL)* | — |
| 5 | Container Scanning | *(planned — Trivy on `flowday-backend` image)* | — |
| 6 | License Compliance | *(planned — pip-licenses + license-checker)* | — |
| 7 | Security Acceptance Criteria | Checklist in this DoD + PR template | human review |
| 8 | SBOM | *(planned — CycloneDX via `cyclonedx-py` / `@cyclonedx/cdxgen`)* | — |

Gates 1, 2, 3, and 7 are **required for merge**. Failing any of them blocks the
PR regardless of functional correctness.
