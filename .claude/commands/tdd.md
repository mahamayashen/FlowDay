# /tdd — Strict RED/GREEN/REFACTOR Cycle

You are executing a strict AI-TDD cycle for FlowDay. Follow these rules EXACTLY.

## Input

The user will provide: issue number and the acceptance criterion to implement.
If not provided, ask: "Which issue number and which acceptance criterion?"

## Cycle Rules

For EACH acceptance criterion, execute exactly 3 steps in order:

### Step 1: RED — Write Failing Test

1. Write the test FIRST in the appropriate `backend/tests/` location (mirror `backend/app/` structure)
2. Test naming: `test_<what>_<expected_outcome>`
3. Run the test: `cd backend && pytest tests/<path>::<test_name> -x -v`
4. **VERIFY the test FAILS** — if it passes, the test is wrong. Fix it until it fails for the right reason.
5. Commit with exact format:
   ```
   git add <test_file>
   git commit -m "[#N][RED] add failing test: <description>"
   ```

### Step 2: GREEN — Minimum Implementation

1. Write the MINIMUM code to make the failing test pass — no extra features, no cleanup
2. Run the test again: `cd backend && pytest tests/<path>::<test_name> -x -v`
3. **VERIFY the test PASSES** — if it fails, fix the implementation (not the test)
4. Run ALL tests to check for regressions: `cd backend && pytest -x -q`
5. Commit with exact format:
   ```
   git add <implementation_files>
   git commit -m "[#N][GREEN] implement: <description>"
   ```

### Step 3: REFACTOR — Clean Up

1. Refactor the code: extract functions, improve naming, remove duplication
2. Do NOT change behavior — do NOT add new features
3. Run ALL tests: `cd backend && pytest -x -q`
4. **VERIFY all tests still pass** — if any fail, your refactor broke something. Fix it.
5. Commit with exact format:
   ```
   git add <refactored_files>
   git commit -m "[#N][REFACTOR] refactor: <description>"
   ```

## After All Cycles Complete

1. Run linting: `cd backend && ruff check . && ruff format .`
2. Fix any lint issues and commit: `[#N][REFACTOR] fix lint issues`
3. Run mutation testing: `cd backend && mutmut run --paths-to-mutate=app/<module>.py`
4. Check results: `cd backend && mutmut results`
5. Target: ≥ 80% mutation score (killed / total mutants)
6. If below 80%, add more tests to kill surviving mutants

## Property-Based Testing

For core business logic, include at least one `@given` hypothesis test:
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=100))
def test_<property>_with_random_input(value):
    # Assert invariant holds for all inputs
```

## CRITICAL RULES

- NEVER write implementation before the failing test
- NEVER skip the RED step — always verify the test fails first
- NEVER add features during REFACTOR — only clean up
- NEVER commit without running tests
- ALWAYS use the `[#N][RED|GREEN|REFACTOR]` commit prefix
- ONE cycle per acceptance criterion — do not batch
