from __future__ import annotations

from datetime import date

import pytest

from app.services.analytics_service import align_to_monday


# ---------------------------------------------------------------------------
# Cycle 1 — align_to_monday
# ---------------------------------------------------------------------------


def test_align_to_monday_already_monday() -> None:
    assert align_to_monday(date(2026, 4, 13)) == date(2026, 4, 13)


def test_align_to_monday_from_wednesday() -> None:
    assert align_to_monday(date(2026, 4, 15)) == date(2026, 4, 13)


def test_align_to_monday_from_sunday() -> None:
    assert align_to_monday(date(2026, 4, 19)) == date(2026, 4, 13)
