from __future__ import annotations

from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


# ── Standard integration tests (require running PostgreSQL) ───────────────────

async def test_get_db_yields_async_session() -> None:
    """get_db must yield an AsyncSession — RED until database.py exists."""
    from app.core.database import get_db

    async for session in get_db():
        assert isinstance(session, AsyncSession)
        break


async def test_session_can_execute_select_1() -> None:
    """The yielded session must be able to run a trivial query against the DB."""
    from app.core.database import get_db

    async for session in get_db():
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        break


# ── Property-based test (no DB connection needed) ─────────────────────────────

@given(
    host=st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Nd"),
            whitelist_characters="-",
        ),
        min_size=1,
        max_size=30,
    ),
    port=st.integers(min_value=1024, max_value=65535),
    dbname=st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Nd"),
            whitelist_characters="_",
        ),
        min_size=1,
        max_size=30,
    ),
)
@h_settings(max_examples=50)
def test_create_async_engine_accepts_valid_asyncpg_url(
    host: str, port: int, dbname: str
) -> None:
    """create_async_engine must not raise for any valid asyncpg URL shape.

    This is a property-based test: hypothesis generates 50 random (host, port,
    dbname) combinations and verifies the engine constructor never raises.
    Engine construction is URL-parsing only — no network connection is made.
    """
    url = f"postgresql+asyncpg://user:pass@{host}:{port}/{dbname}"
    engine = create_async_engine(url)
    assert engine is not None
