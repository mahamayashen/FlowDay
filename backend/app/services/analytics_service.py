from __future__ import annotations

from app.schemas.analytics import StatusTag


def compute_status_tag(planned_hours: float, actual_hours: float) -> StatusTag:
    """Determine the status tag for a single task comparison.

    Pure function — no DB access.
    """
    if planned_hours > 0:
        if actual_hours >= 0.9 * planned_hours:
            return StatusTag.DONE
        if actual_hours > 0:
            return StatusTag.PARTIAL
        return StatusTag.SKIPPED
    if actual_hours > 0:
        return StatusTag.UNPLANNED
    return StatusTag.SKIPPED
