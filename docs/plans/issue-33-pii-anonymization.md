# Issue #33 — PII Anonymization Layer for LLM Calls

## Goal

Add middleware to strip/anonymize PII before sending data to LLM providers, with a de-anonymization map to restore original values in output.

## Architecture

New module: `backend/app/agents/anonymizer.py`

### PII Detection

Detect these PII categories using regex + heuristic matching:
- **Emails**: regex pattern for email addresses
- **Names**: proper nouns in task titles / project names (treated as potential client/person names)
- **Financial data**: dollar amounts, hourly rates
- **UUIDs**: user IDs, task IDs (already in deps but shouldn't leak to LLM)

### Anonymization Strategy

Replace detected PII with deterministic tokens:
- Emails → `[EMAIL_1]`, `[EMAIL_2]`, ...
- Project names → `[PROJECT_1]`, `[PROJECT_2]`, ...
- Task titles → `[TASK_1]`, `[TASK_2]`, ...
- Dollar amounts → `[AMOUNT_1]`, `[AMOUNT_2]`, ...
- UUIDs → stripped entirely (not needed by LLM for analysis)

### Core Classes

```python
class PIIAnonymizer:
    """Stateful anonymizer that tracks token↔original mappings."""
    _mapping: dict[str, str]       # token → original
    _reverse: dict[str, str]       # original → token
    _counters: dict[str, int]      # category → next counter

    def anonymize_text(self, text: str) -> str
    def deanonymize_text(self, text: str) -> str
    def anonymize_deps(self, deps: T) -> T       # deep-copy + anonymize string fields
    def deanonymize_result(self, result: T) -> T  # restore tokens in result strings
    def get_audit_log(self) -> list[dict]          # what was anonymized (categories + counts, no PII)
```

### Integration Point

In `run_with_metrics()` in `base.py` — wrap the agent call:
1. Create `PIIAnonymizer` instance
2. Anonymize deps before passing to `agent.run()`
3. De-anonymize the result output
4. Log audit entry

This is the single chokepoint where all agents are invoked, so one integration point covers the entire pipeline.

## TDD Cycles

### Cycle 1: PII Detection
- **RED**: Test that detector finds emails, dollar amounts, UUIDs in text
- **GREEN**: Implement regex-based `detect_pii()` returning categorized matches
- **REFACTOR**: Extract patterns to constants

### Cycle 2: Anonymization / De-anonymization
- **RED**: Test `anonymize_text` replaces PII with tokens; `deanonymize_text` restores originals
- **GREEN**: Implement `PIIAnonymizer` with bidirectional mapping
- **REFACTOR**: Clean up

### Cycle 3: Deps Anonymization
- **RED**: Test `anonymize_deps` on `TimeAnalystDeps` / `TaskAnalystDeps` replaces PII fields
- **GREEN**: Implement deep-copy + field-level anonymization for agent deps dataclasses
- **REFACTOR**: Generalize across all deps types

### Cycle 4: Pipeline Integration + Audit Logging
- **RED**: Test that `run_with_metrics` applies anonymization and logs audit entry
- **GREEN**: Wire anonymizer into `run_with_metrics()`
- **REFACTOR**: Final cleanup

## Acceptance Criteria

- [x] PII detection: emails, names, client names, financial data
- [x] Anonymization: replace with tokens (`[PROJECT_1]`, `[EMAIL_1]`, etc.)
- [x] De-anonymization map restores original values in output
- [x] All LLM inputs pass through anonymizer (via `run_with_metrics`)
- [x] Audit logging of what was anonymized (categories + counts, no PII)
- [x] Unit tests for detection and anonymization logic

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/app/agents/anonymizer.py` | **Create** — core anonymization module |
| `backend/app/agents/base.py` | **Modify** — integrate anonymizer into `run_with_metrics` |
| `backend/tests/unit/agents/test_anonymizer.py` | **Create** — unit tests |
