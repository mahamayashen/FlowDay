from __future__ import annotations

from datetime import date

import pytest

from app.services.analytics_service import align_to_monday, compute_accuracy_pct


# ---------------------------------------------------------------------------
# Cycle 1 — align_to_monday
# ---------------------------------------------------------------------------


def test_align_to_monday_already_monday() -> None:
    assert align_to_monday(date(2026, 4, 13)) == date(2026, 4, 13)


def test_align_to_monday_from_wednesday() -> None:
    assert align_to_monday(date(2026, 4, 15)) == date(2026, 4, 13)


def test_align_to_monday_from_sunday() -> None:
    assert align_to_monday(date(2026, 4, 19)) == date(2026, 4, 13)


# ---------------------------------------------------------------------------
# Cycle 2 — compute_accuracy_pct
# ---------------------------------------------------------------------------


def test_accuracy_pct_normal_case() -> None:
    assert compute_accuracy_pct(2.0, 1.5) == 75.0


def test_accuracy_pct_zero_planned() -> None:
    assert compute_accuracy_pct(0.0, 1.5) == 0.0


def test_accuracy_pct_over_100_percent() -> None:
    assert compute_accuracy_pct(2.0, 4.0) == 200.0


def test_accuracy_pct_exact_match() -> None:
    assert compute_accuracy_pct(3.0, 3.0) == 100.0
