from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import dispose_engine, init_engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
async def db_engine():
    """Initialise the async engine once for the whole test session."""
    init_engine()
    yield
    await dispose_engine()


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP client wired directly to the FastAPI app (no network)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
