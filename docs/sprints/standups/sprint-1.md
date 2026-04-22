# Sprint 1 Async Standups

## @mahamayashen — 2026-03-22

**Yesterday:** —  
**Today:** Initial project setup — FastAPI skeleton (#1), PostgreSQL + SQLAlchemy async + Alembic (#2), CLAUDE.md with @imports  
**Blockers:** None

## @EvanjyChen — 2026-03-22

**Yesterday:** —  
**Today:** Setting up Claude Code configuration — CLAUDE.md, permissions, data model docs, conventions doc  
**Blockers:** None

---

## @mahamayashen — 2026-03-30

**Yesterday:** Project skeleton and DB config merged  
**Today:** Starting User model + OAuth 2.0 + JWT auth (#3) — TDD: writing failing tests for Fernet encryption, JWT create/decode, User model  
**Blockers:** Need Google/GitHub OAuth app credentials for callback testing

## @EvanjyChen — 2026-03-31

**Yesterday:** Reviewed PR #11 for User auth  
**Today:** Helping debug OAuth callback flow, reviewing Fernet encryption approach  
**Blockers:** None

---

## @mahamayashen — 2026-04-05

**Yesterday:** User auth merged (PR #12)  
**Today:** Adding custom Claude Code skills — `/review-pr` (v1) and `/review-pr-v2` with dependency audit and test coverage gap detection  
**Blockers:** None

## @EvanjyChen — 2026-04-12

**Yesterday:** Skills and hooks committed  
**Today:** Addressing PR review feedback on #3 — httpx as prod dep, refresh user check, upsert RETURNING clause  
**Blockers:** None

---

## @mahamayashen — 2026-04-13

**Yesterday:** Auth PR feedback addressed  
**Today:** Implementing Project CRUD (#4) and Task CRUD (#5) — writing RED tests for model, schemas, service, and routes. Also starting Docker Compose (#6) and CI pipeline (#7)  
**Blockers:** None

## @EvanjyChen — 2026-04-13

**Yesterday:** —  
**Today:** Reviewing PRs #13, #14 for Project and Task CRUD. Running `/review-pr-v2` on both.  
**Blockers:** None

---

## @mahamayashen — 2026-04-14

**Yesterday:** Project + Task CRUD done, Docker Compose up  
**Today:** Finishing CI pipeline (#7), Sentry + health monitoring (#8), integration tests (#9). Merging PRs #15, #16.  
**Blockers:** None

## @EvanjyChen — 2026-04-14

**Yesterday:** Reviewed Docker and CI PRs  
**Today:** Validating CI pipeline runs green on GitHub Actions. Planning Sprint 2 issues.  
**Blockers:** None
