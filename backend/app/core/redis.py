from __future__ import annotations

from redis.asyncio import Redis, from_url

_redis: Redis | None = None


async def init_redis(url: str) -> None:
    """Create the async Redis client. Called once from the FastAPI lifespan."""
    global _redis
    _redis = from_url(url)


async def close_redis() -> None:
    """Close the async Redis client. Called once from the FastAPI lifespan."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis:
    """Return the Redis client or raise if not initialised."""
    if _redis is None:
        raise RuntimeError("Redis client not initialised. Call init_redis() first.")
    return _redis
