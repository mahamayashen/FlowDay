from __future__ import annotations

import pytest

from app.core.redis import close_redis, get_redis, init_redis


def test_get_redis_before_init_raises() -> None:
    """get_redis() must raise RuntimeError when called before init_redis()."""
    with pytest.raises(RuntimeError, match="Redis client not initialised"):
        get_redis()


@pytest.mark.anyio
async def test_init_redis_creates_client() -> None:
    """After init_redis(), get_redis() must return a Redis client."""
    try:
        await init_redis("redis://localhost:6379/0")
        client = get_redis()
        assert client is not None
    finally:
        await close_redis()


@pytest.mark.anyio
async def test_close_redis_clears_client() -> None:
    """After close_redis(), get_redis() must raise RuntimeError again."""
    await init_redis("redis://localhost:6379/0")
    await close_redis()
    with pytest.raises(RuntimeError, match="Redis client not initialised"):
        get_redis()
