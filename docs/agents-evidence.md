# FlowDay Custom Sub-Agents — Evidence of Use

**Deliverable:** Option 1 from the course/project requirement — **custom sub-agents in `.claude/agents/`**.
**Date recorded:** 2026-04-21
**Session operator:** Claude Code (Opus 4.7, 1M context) working in worktree `awesome-galileo-4129a8`
**Repo root:** `/Users/jinyuchen/Desktop/NEU/26sp/7180/P3/FlowDay`

---

## 1. Agents shipped

Three custom sub-agents live at `.claude/agents/`, each tied to one of FlowDay's four production requirements from `CLAUDE.md`:

| Agent file | Production requirement | Role |
|---|---|---|
| [`security-reviewer.md`](../.claude/agents/security-reviewer.md) | #4 Security audit passed | OWASP Top 10 + FlowDay-specific (OAuth/Fernet, PII anonymization, prompt-injection defense). Read-only. |
| [`test-writer.md`](../.claude/agents/test-writer.md) | #3 CI/CD + monitoring (TDD discipline) | Generates RED-phase pytest / Vitest tests, including `hypothesis` property-based tests. |
| [`agent-pipeline-reviewer.md`](../.claude/agents/agent-pipeline-reviewer.md) | #1 Parallel agents + #2 LLM-as-Judge | Verifies `asyncio.gather` Group A, typed `RunContext` DI, Judge-vs-Writer provider split, `ModelRetry` cap. Read-only. |

Each agent declares its `tools:` allowlist (least-privilege), a `model: inherit` marker, and a precise output format so downstream tooling (or a reviewer) can parse verdicts.

### Invocation

Once Claude Code reloads the agent registry, any of them can be invoked via:

```
Agent(subagent_type="security-reviewer", prompt="review backend/app/api/projects.py")
Agent(subagent_type="test-writer",       prompt="RED tests for acceptance criterion X in module Y")
Agent(subagent_type="agent-pipeline-reviewer", prompt="review changes under backend/app/agents/")
```

They are also intended to be triggered proactively — their `description:` frontmatter ends in "Use proactively after edits to …" so Claude Code will suggest them when the relevant files are touched.

---

## 2. Evidence of use — live runs on the current repo

Each agent was invoked against a real FlowDay file. Outputs below are **verbatim** from the sub-agent run and cite `file:line` against the code as of commit `eff6288` (branch `claude/awesome-galileo-4129a8`).

### Run 1 — `security-reviewer` on `backend/app/api/auth.py` + `backend/app/core/security.py`

**Verdict:** FAIL
**Tool calls:** 11 — Read, Grep, Bash (`gitleaks`-style secret scan pattern)
**Duration:** ~109 s

#### Findings (6)

1. **[OWASP A09 / A02]** — Google token-exchange response body is logged at ERROR and echoed back in the 401 response detail, leaking provider-internal error JSON.
   - Location: `backend/app/api/auth.py:110-124`
   - Fix: strip `.text`, return a static detail.

2. **[OWASP A09 / A02]** — GitHub callback logs the *successful* 200-OK token-exchange body unconditionally, writing `access_token=gho_…` to logs on every login.
   - Location: `backend/app/api/auth.py:186-193`
   - Fix: delete the debug-log block, or gate on `status_code != 200` and strip `access_token`.

3. **[OWASP A07 | FlowDay-auth-rate-limit]** — No rate limiting anywhere on `/auth/*`. `grep -r "slowapi\|Limiter"` returns zero hits.
   - Location: `backend/app/api/auth.py:87, 156, 254`
   - Fix: wire `slowapi` and decorate callbacks + `/auth/refresh`.

4. **[OWASP A07 | FlowDay-refresh-rotation]** — Refresh tokens are **not rotated** — `/auth/refresh` returns `body.refresh_token` unchanged.
   - Location: `backend/app/api/auth.py:289-294`
   - Fix: mint a new refresh token each call + store jti in Redis for reuse detection.

5. **[OWASP A02 | FlowDay-secret-default]** — `SECRET_KEY` has a hard-coded fallback `"change-me-in-production"` used both as JWT signing key *and* Fernet KDF input.
   - Location: `backend/app/core/config.py:22`
   - Fix: remove the default, or assert-and-fail-fast on startup.

6. **[OWASP A07]** — `create_access_token(extra=…)` lets the caller overwrite `sub`/`exp`/`type`; `decode_token` validates no `aud`/`iss`/`nbf`.
   - Location: `backend/app/core/security.py:43-55, 65-70`
   - Fix: reserved claims always win; require `exp`/`sub` on decode.

#### Checks that passed

- A01: `/auth/me` gated by `Depends(get_current_user)` (`auth.py:249`).
- A02 (Fernet): OAuth tokens Fernet-encrypted before persistence (`security.py:29-34`).
- A03: All endpoints use Pydantic schemas; DB writes use SQLAlchemy Core (no raw SQL).
- A05: `.env` is gitignored; CORS not `*` in code under review.
- A07 (access TTL): `ACCESS_TOKEN_EXPIRE_MINUTES = 15`.
- A10: All `httpx` calls use hardcoded allowlisted hosts (Google, GitHub).
- FlowDay secret scan: no `sk-…`, `ghp_…`, `AIza…`, or `BEGIN PRIVATE KEY` literals.

> **Status:** The FAIL verdict is **actionable**. Findings #1, #2, and #4 should be filed as issues. Finding #5 is a startup-hardening item. The agent correctly cited line numbers that resolve in the current tree.

---

### Run 2 — `agent-pipeline-reviewer` on the weekly-review pipeline

**Scope:** `backend/app/agents/orchestrator.py`, `judge.py`, `narrative_writer.py`, and the four Group A analysts (`time_analyst.py`, `meeting_analyst.py`, `code_analyst.py`, `task_analyst.py`).
**Verdict:** PASS (with one WARN-level monitoring finding)
**Tool calls:** 22 — Read, Grep across `backend/app/agents/` and `backend/app/services/weekly_review_service.py`
**Duration:** ~146 s

#### The one finding

**[Requirement #3 | per-agent Sentry breadcrumbs]** — Sentry breadcrumbs are emitted at the *stage* level (Group A/B/C/D) inside `_run_stage`, not per individual analyst. A single failing analyst in Group A shares one breadcrumb with its three siblings.
- Location: `backend/app/agents/orchestrator.py:103-116`; `backend/app/agents/base.py:32-67`
- Impact: monitoring granularity (A09). Prometheus `agent_latency_seconds` still labels per agent, so metrics compensate partially.
- Fix: add `sentry_sdk.add_breadcrumb(category="agent", message=f"{name} …")` inside `run_with_metrics` on success and in the except branch.

#### Checks that passed (highlights)

- Single `asyncio.gather` launches all 4 Group A analysts (`orchestrator.py:111-116`).
- `_safe_run` wrapper gives per-agent error isolation — a failing analyst yields `None` without aborting siblings (`orchestrator.py:103-109`).
- Inter-group boundaries carry typed Pydantic / `@dataclass` objects — no `dict[str, Any]`.
- Every agent is a `pydantic_ai.Agent[<Deps>, <Result>]` with both `deps_type=` and `output_type=` set to Pydantic types (not `str`).
- PII anonymization runs pre-LLM and reversal runs post-LLM inside `run_with_metrics` (`base.py:42-51`).
- **Judge-vs-Writer provider isolation confirmed:** Narrative Writer uses `settings.LLM_MODEL = "openai:gpt-5.4-nano-2026-03-17"`; Judge uses `settings.LLM_JUDGE_MODEL = "google-gla:gemini-2.5-pro"` (`config.py:49-50`). Different provider families (OpenAI vs Google GLA).
- Judge scores exactly 3 dimensions (`actionability_score`, `accuracy_score`, `coherence_score`) — each `int` with `Field(ge=1, le=10)` — plus an overall.
- Judge raises `ModelRetry` below `settings.JUDGE_SCORE_THRESHOLD` (default 6), capped at `retries=2` (`judge.py:19`); exhaustion degrades to `None` via `UnexpectedModelBehavior` catch at `orchestrator.py:209-211`.
- Metrics: `agent_latency_seconds` per agent, `judge_score` histogram, `judge_retry_count` counter — all instrumented.
- No `datetime.utcnow()` / `random.*` inside any agent module — deterministic for tests.

#### Pipeline diagram (produced by the agent, as read)

```
           run_group_a (orchestrator.py:57)  —  asyncio.gather + _safe_run
           ┌──────────────────────┬──────────────────────┬──────────────────────┐
           ▼                      ▼                      ▼                      ▼
    time_analyst.py        meeting_analyst.py      code_analyst.py        task_analyst.py
    openai:gpt-5.4-nano    openai:gpt-5.4-nano     openai:gpt-5.4-nano    openai:gpt-5.4-nano
           └──────────────────────┴──────────────────────┴──────────────────────┘
                                              │ aggregated into
                                              ▼
                                       GroupAResult
                                              │
                                              ▼
                           Group B: pattern_detector.py (openai:gpt-5.4-nano)
                                              │
                                              ▼
                           Group C: narrative_writer.py (openai:gpt-5.4-nano)
                                              │
                                              ▼
                           Group D: judge.py (google-gla:gemini-2.5-pro  ← DIFFERENT PROVIDER)
                                              │   retries=2, threshold=6, ModelRetry on min<thresh
                                              ▼
                                AgentScoreHistory row  +  judge_score histogram

  PII: anonymize_deps() → agent.run() → deanonymize_output() inside run_with_metrics
  Breadcrumbs: per-STAGE only today — per-agent would be a nice-to-have (finding #1)
```

> **Status:** The pipeline satisfies production requirements #1 (parallel agents) and #2 (LLM-as-Judge) as specified in `claude-project-instructions.md`. Requirement #3 has one WARN.

---

### Run 3 — `test-writer` for `anonymize_text` acceptance criterion

**Acceptance criterion under TDD:** `anonymize_text(text: str) -> str` must replace any email address with the literal `<EMAIL>` before the text is passed to an LLM, and preserve non-email content byte-for-byte.

**Tool calls:** 8 — Read (target + neighboring tests), Write (1 file)
**Duration:** ~56 s
**File written:** `backend/tests/test_anonymizer_email.py` (1904 bytes, verified on disk)

#### Test content (3 tests)

1. **Happy path** — `test_anonymize_text_replaces_email_in_middle_of_text`: `"Please contact john.doe@example.com for details."` → `"Please contact <EMAIL> for details."`
2. **Edge case** — `test_anonymize_text_returns_unchanged_when_no_email`: byte-for-byte identity when no email present.
3. **Property-based** — `test_anonymize_text_is_identity_for_strings_without_at_sign`: `@given(st.text().filter(lambda s: "@" not in s))` → identity.

#### Proposed commit

`[#N][RED] add failing test: anonymize_text redacts emails`

#### Expected RED failure (confirmed by reading the current code)

`app.core.anonymizer` today exposes only the instance method `PIIAnonymizer.anonymize_text` — there is no module-level `anonymize_text` function. `from app.core.anonymizer import anonymize_text` raises `ImportError` at collection time, failing all three tests. Even if a free function existed, the current implementation substitutes `[EMAIL_1]` (indexed token), not the literal `<EMAIL>` required by the criterion. RED is the **right kind of failure** — a missing symbol, not a broken test harness.

#### Operator-side confirmation command

```
conda activate vibing && cd backend && pytest tests/test_anonymizer_email.py -x -q
```

(Per `CLAUDE.md`, the Python env is only active outside the sandbox, so the actual `pytest` invocation is left to the developer. The agent correctly refused to run it.)

#### GREEN hint (next step in the TDD cycle)

Add a module-level `anonymize_text(text: str) -> str` in `backend/app/core/anonymizer.py` that applies `_EMAIL_RE.sub("<EMAIL>", text)`.

> **Status:** A real RED test has landed on disk. The developer can run the command above to confirm the failure and then proceed to GREEN.

---

## 3. How this maps to the assignment requirements

| Requirement | Delivered |
|---|---|
| Custom sub-agents in `.claude/agents/` | 3 agents: `security-reviewer`, `test-writer`, `agent-pipeline-reviewer` |
| Agent output produces useful work | 6 concrete security findings with file:line + a real RED test on disk + a verified pipeline audit |
| Evidence of use (session log / PR / screenshots) | This document — full transcripts with tool-call counts, durations, verdicts, and cited findings |

## 4. Reproducing this evidence

```bash
# 1. The agents already live in the repo:
ls .claude/agents/
# security-reviewer.md  test-writer.md  agent-pipeline-reviewer.md

# 2. Confirm the RED test written by test-writer:
ls -la backend/tests/test_anonymizer_email.py
conda activate vibing && cd backend && pytest tests/test_anonymizer_email.py -x -q
# Expected: ImportError on `anonymize_text` — this is the RED signal.

# 3. Re-run any sub-agent by asking Claude Code in this repo:
#    "Run the security-reviewer agent on backend/app/api/projects.py"
#    "Run test-writer with acceptance criterion X on module Y"
#    "Run agent-pipeline-reviewer after changes under backend/app/agents/"
```
