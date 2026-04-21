---
name: Feature
about: A new capability or enhancement planned through the 4-phase workflow
title: "<short imperative title>"
labels: ["enhancement"]
---

<!--
Feature issues drive the 4-phase workflow enforced by CLAUDE.md:
  Explore  → /explore-issue
  Plan     → /plan-issue (writes docs/plans/issue-<N>-<name>.md)
  Implement → /tdd (strict RED/GREEN/REFACTOR, one cycle per AC below)
  Commit   → feature/<issue-number>-<name> branch → PR to main
Fill every section before moving to Phase 2.
-->

## Description
<!-- What is this feature and why does it exist? What user / system problem does it solve? -->

## Acceptance Criteria
<!--
One checkbox per TDD cycle. Each item must be small enough that a single
failing test can anchor it. Avoid compound criteria joined by "and".
-->
- [ ]
- [ ]
- [ ]

## Production Requirement Link
<!-- Which of the four production requirements does this connect to? Delete rows that don't apply. -->
- [ ] Parallel agents (Group A `asyncio.gather`, per-agent error handling)
- [ ] LLM-as-Judge (different provider from Narrative Writer, retry on score < 80)
- [ ] CI/CD + monitoring (Sentry breadcrumbs, Grafana metrics, mutmut ≥ 80%)
- [ ] Security (OAuth token encryption, PII anonymisation before LLM, scoping)

## Scope
**In scope:**
-

**Out of scope (flag if encountered):**
-

## TDD Cycles
<!-- One entry per acceptance criterion. -->
1. **RED:** <failing test that anchors AC #1>
   **GREEN:** <minimum implementation to pass>
   **REFACTOR:** <cleanup target>
2.
3.

## References
<!-- Links to related issues, design docs, external specs. -->
-
