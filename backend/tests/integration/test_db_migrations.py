from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent.parent  # tests/integration/ → backend/


def test_alembic_upgrade_head_runs_without_error() -> None:
    """alembic upgrade head must exit 0 — RED until alembic.ini and env.py exist."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stderr}"


def test_alembic_current_returns_a_revision_after_upgrade() -> None:
    """alembic current must show a revision at (head) — RED until migrations exist."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR,
    )
    assert result.returncode == 0, f"alembic current failed:\n{result.stderr}"
    assert "(head)" in result.stdout, (
        f"Expected a revision at head, got:\n{result.stdout}"
    )
