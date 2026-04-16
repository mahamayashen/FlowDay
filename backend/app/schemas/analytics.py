from __future__ import annotations

import enum


class StatusTag(enum.StrEnum):
    """Planned-vs-actual comparison status for a task."""

    DONE = "done"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    UNPLANNED = "unplanned"
