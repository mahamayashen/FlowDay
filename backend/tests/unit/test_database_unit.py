"""Unit tests for app/core/database.py targeting mutation coverage.

These tests do not require a running PostgreSQL instance — they verify
the structural configuration of the engine and session factory, and the
control flow of init/dispose/get_db.
"""
from __future__ import annotations

from app.core import database
from app.core.database import dispose_engine, get_db, init_engine

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _reset() -> None:
    """Dispose and reset module-level state between tests."""
    await dispose_engine()


# ── init_engine configuration (kills mutants 5, 7) ───────────────────────────

async def test_init_engine_enables_pool_pre_ping() -> None:
    """Engine must be created with pool_pre_ping=True (kills mutant 5).

    pool_pre_ping sends a lightweight SELECT before each checkout to detect
    stale connections. Turning it off causes silent failures after DB restarts.
    """
    engine = init_engine()
    try:
        assert engine.pool._pre_ping is True
    finally:
        await dispose_engine()


async def test_init_engine_disables_expire_on_commit() -> None:
    """Session factory must have expire_on_commit=False (kills mutant 7).

    With async sessions, expire_on_commit=True would trigger lazy-loads after
    commit, which raise MissingGreenlet errors in async code.
    """
    init_engine()
    try:
        assert database._session_factory is not None
        assert database._session_factory.kw.get("expire_on_commit") is False
    finally:
        await dispose_engine()


# ── dispose_engine control flow (kills mutants 9, 10, 11) ────────────────────

async def test_dispose_engine_sets_engine_to_none() -> None:
    """After dispose, _engine must be exactly None, not falsy (kills mutants 9, 10)."""
    init_engine()
    await dispose_engine()
    assert database._engine is None


async def test_dispose_engine_sets_session_factory_to_none() -> None:
    """After dispose, _session_factory must be exactly None (kills mutants 9, 11)."""
    init_engine()
    await dispose_engine()
    assert database._session_factory is None


async def test_dispose_engine_when_not_initialized_does_not_raise() -> None:
    """dispose_engine must be safe to call when engine is already None."""
    database._engine = None
    database._session_factory = None
    await dispose_engine()  # must not raise


# ── Initial state (kills mutants 2, 4) ───────────────────────────────────────

async def test_after_dispose_engine_initial_state_is_none() -> None:
    """_engine and _session_factory must be None after dispose (kills mutants 2, 4)."""
    init_engine()
    await dispose_engine()
    assert database._engine is None
    assert database._session_factory is None


# ── get_db error message (kills mutant 13) ────────────────────────────────────

async def test_get_db_raises_runtime_error_with_correct_message() -> None:
    """get_db must raise RuntimeError with the exact message (kills mutant 13)."""
    database._engine = None
    database._session_factory = None

    error_raised: RuntimeError | None = None
    try:
        async for _ in get_db():
            pass
    except RuntimeError as exc:
        error_raised = exc

    assert error_raised is not None, "Expected RuntimeError was not raised"
    assert str(error_raised) == (
        "Database engine not initialised. Call init_engine() first."
    )


def test_module_initial_state_is_none_before_init() -> None:
    """Module-level defaults must be None, not '' (kills mutants 2, 4)."""
    import importlib

    import app.core.database as db_mod

    # Capture current state, reset to initial, verify, then restore
    saved_engine = db_mod._engine
    saved_factory = db_mod._session_factory

    importlib.reload(db_mod)
    try:
        assert db_mod._engine is None
        assert db_mod._session_factory is None
    finally:
        # Restore previous state so other tests aren't affected
        db_mod._engine = saved_engine
        db_mod._session_factory = saved_factory
