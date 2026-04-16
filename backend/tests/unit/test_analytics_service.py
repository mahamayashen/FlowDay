from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from app.schemas.analytics import StatusTag
from app.services.analytics_service import compute_status_tag


# ---------------------------------------------------------------------------
# compute_status_tag — deterministic tests
# ---------------------------------------------------------------------------


def test_compute_status_tag_done_exact_match() -> None:
    """100% of planned → done."""
    assert compute_status_tag(2.0, 2.0) == StatusTag.DONE


def test_compute_status_tag_done_at_threshold() -> None:
    """Exactly 90% of planned → done."""
    assert compute_status_tag(2.0, 1.8) == StatusTag.DONE


def test_compute_status_tag_done_over_planned() -> None:
    """More actual than planned → done."""
    assert compute_status_tag(2.0, 3.0) == StatusTag.DONE


def test_compute_status_tag_partial() -> None:
    """Less than 90% of planned → partial."""
    assert compute_status_tag(2.0, 1.0) == StatusTag.PARTIAL


def test_compute_status_tag_partial_just_below_threshold() -> None:
    """Just under 90% → partial."""
    assert compute_status_tag(2.0, 1.79) == StatusTag.PARTIAL


def test_compute_status_tag_skipped() -> None:
    """Planned but zero actual → skipped."""
    assert compute_status_tag(2.0, 0.0) == StatusTag.SKIPPED


def test_compute_status_tag_unplanned() -> None:
    """No plan but has actual → unplanned."""
    assert compute_status_tag(0.0, 1.5) == StatusTag.UNPLANNED


# ---------------------------------------------------------------------------
# compute_status_tag — property-based tests
# ---------------------------------------------------------------------------


@given(
    planned=st.floats(min_value=0.01, max_value=100.0),
    ratio=st.floats(min_value=0.9, max_value=10.0),
)
def test_status_tag_done_property(planned: float, ratio: float) -> None:
    """Any actual >= 90% of planned is done."""
    actual = planned * ratio
    assert compute_status_tag(planned, actual) == StatusTag.DONE


@given(
    planned=st.floats(min_value=0.01, max_value=100.0),
    ratio=st.floats(min_value=0.001, max_value=0.8999),
)
def test_status_tag_partial_property(planned: float, ratio: float) -> None:
    """Any 0 < actual < 90% of planned is partial."""
    actual = planned * ratio
    assert compute_status_tag(planned, actual) == StatusTag.PARTIAL


@given(actual=st.floats(min_value=0.01, max_value=100.0))
def test_status_tag_unplanned_property(actual: float) -> None:
    """Any actual > 0 with zero planned is unplanned."""
    assert compute_status_tag(0.0, actual) == StatusTag.UNPLANNED
