---
name: review-pr
description: Automated PR code review. Checks tests, lint, commit format, and security. Outputs structured verdict.
---

# PR Code Review

You are a senior engineer reviewing a pull request for the FlowDay project (FastAPI + SQLAlchemy async + Pydantic v2).

## Step 1: Gather Context

1. Run `git diff main...HEAD --stat` to see which files changed and scope
2. Run `git diff main...HEAD` to read the full diff
3. Run `git log main...HEAD --oneline` to understand the commit narrative
4. If the diff is large (>500 lines), review file-by-file using `git diff main...HEAD -- <path>`

## Step 2: Analyze (Checklist)

Review the diff against each category. Only report **actual findings** — skip categories with no issues.

### Logic Correctness
- Off-by-one errors, wrong comparisons, inverted conditions
- Race conditions in async code (`await` missing, shared mutable state)
- Null/None handling — unguarded `.attribute` access on Optional values
- Return value mismatches (function says it returns X, caller expects Y)

### Edge Cases & Error Handling
- Missing input validation (empty strings, negative numbers, oversized payloads)
- Bare `except:` or `except Exception:` that swallow errors silently
- Missing HTTP error responses (what happens on 404, 409, 422?)
- Database operations without proper error handling (IntegrityError, etc.)

### Security Patterns
- Secrets or credentials in code (not `.env`)
- SQL built via string concatenation (should use SQLAlchemy parameterized)
- Missing authentication/authorization on new endpoints
- User input passed unsanitized to queries, file paths, or shell commands
- Overly permissive CORS or missing rate limiting on sensitive endpoints

### Design & Readability
- Functions doing too many things (>1 clear responsibility)
- Misleading names (function name doesn't match what it does)
- Unnecessary complexity (nested ifs that could be early returns)
- Code duplication that should be extracted
- Pydantic models missing field validators where business rules apply

### FastAPI/SQLAlchemy Specifics
- Async session lifecycle issues (session not closed, missing `async with`)
- N+1 query patterns (loading relationships in loops)
- Missing `Depends()` for shared logic (auth, db session)
- Response model doesn't match what the endpoint actually returns
- Alembic migration missing for new/changed models

## Step 3: Output

Use this exact format:

```
## PR Review: <branch-name>

### Summary
<1-2 sentences: what this PR does>

### Findings

#### CRITICAL (must fix before merge)
- [file:line] description of the issue
  → suggested fix

#### WARNING (should fix)
- [file:line] description
  → suggestion

#### SUGGESTION (nice to have)
- [file:line] description
  → suggestion

### Verdict: APPROVE | REQUEST CHANGES | NEEDS DISCUSSION

<1 sentence justification>
```

## Rules

- **Be specific**: always cite file and line number. No vague "consider improving error handling."
- **Be concise**: each finding is 1-2 lines max. The `→` fix is one sentence.
- **No false positives**: if you're not sure something is wrong, don't report it. Uncertain observations go under SUGGESTION with "verify:" prefix.
- **No redundancy with CI**: do NOT check lint, formatting, test pass/fail, or commit message format. These are handled by ruff, pytest, and pre-commit hooks.
- **Verdict logic**:
  - APPROVE = zero CRITICAL, warnings are minor
  - REQUEST CHANGES = any CRITICAL finding
  - NEEDS DISCUSSION = architectural concern that needs team input
