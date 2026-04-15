from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from app.core.database import get_db, init_engine
from app.core.security import create_access_token
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def db_engine_sync() -> None:
    """Initialise the global engine once (sync fixture avoids event-loop issues)."""
    init_engine()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired directly to the FastAPI app (no network)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession wrapped in a transaction that rolls back after test.

    Uses the "nested transaction + event listener" pattern from SQLAlchemy docs
    so that service code calling commit()/refresh() works transparently.
    """
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        # After each nested transaction ends, restart a new SAVEPOINT
        # so the next commit in application code works correctly.
        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sync_session: Session, transaction: object) -> None:
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                conn.sync_connection.begin_nested()  # type: ignore[union-attr]

        async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override_get_db

        yield session

        await session.close()
        await conn.rollback()
        app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database and return it."""
    user = User(
        id=uuid.uuid4(),
        email=f"testuser-{uuid.uuid4().hex[:8]}@example.com",
        name="Test User",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create a second user for ownership-scoping tests."""
    user = User(
        id=uuid.uuid4(),
        email=f"otheruser-{uuid.uuid4().hex[:8]}@example.com",
        name="Other User",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def auth_client(
    db_session: AsyncSession, test_user: User
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with a valid JWT for test_user."""
    token = create_access_token(subject=test_user.email)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac


@pytest.fixture
async def other_auth_client(
    db_session: AsyncSession, other_user: User
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with a valid JWT for other_user."""
    token = create_access_token(subject=other_user.email)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
