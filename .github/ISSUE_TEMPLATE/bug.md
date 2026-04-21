---
name: Bug
about: Something is broken or behaves incorrectly
title: "<short description of the broken behaviour>"
labels: ["bug"]
---

<!--
Bug issues still follow the 4-phase workflow: Explore the failure, Plan a fix
with a regression test as the first AC, Implement via /tdd, then Commit on a
feature branch named fix/<issue-number>-<short-name>.
-->

## What happened
<!-- Observed behaviour. Include stack traces, screenshots, or response bodies verbatim. -->

## What should have happened
<!-- Expected behaviour and why. Reference the AC or design doc that says so if relevant. -->

## Steps to reproduce
1.
2.
3.

## Environment
- **Branch / commit:**
- **Backend env:** Python version, DB state, migrations applied
- **Frontend env:** browser, Node version
- **Relevant feature flags:**

## Impact
- [ ] Data corruption or loss
- [ ] Security / auth bypass
- [ ] Crash on critical path
- [ ] Incorrect output (no data at risk)
- [ ] UX only / cosmetic

## Regression test
<!--
The first acceptance criterion for any bug fix must be a failing test that
reproduces the bug. Draft it here before implementing the fix.
-->
- [ ] Failing test at `<path>::<test_name>` reproduces the bug

## Scope
**In scope for the fix:**
-

**Out of scope (file separately):**
-
