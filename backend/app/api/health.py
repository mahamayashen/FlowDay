from __future__ import annotations

import logging
import time
from importlib.metadata import version

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.health import (
    DependencyDetail,
    DetailedHealthResponse,
    HealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_HEALTH_CHECK_ERRORS = (OSError, ConnectionError, TimeoutError, RuntimeError)


async def _check_db(db: AsyncSession) -> tuple[str, float]:
    """Check database connectivity. Returns (status, latency_ms)."""
    start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        status = "healthy"
    except _HEALTH_CHECK_ERRORS:
        logger.warning("Database health check failed", exc_info=True)
        status = "unhealthy"
    latency = round((time.monotonic() - start) * 1000, 2)
    return status, latency


async def _check_redis() -> tuple[str, float]:
    """Check Redis connectivity. Returns (status, latency_ms)."""
    start = time.monotonic()
    try:
        redis = get_redis()
        await redis.ping()  # type: ignore[misc]
        status = "healthy"
    except _HEALTH_CHECK_ERRORS:
        logger.warning("Redis health check failed", exc_info=True)
        status = "unhealthy"
    latency = round((time.monotonic() - start) * 1000, 2)
    return status, latency


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return application health status including DB and Redis connectivity."""
    db_status, _ = await _check_db(db)
    redis_status, _ = await _check_redis()

    all_healthy = db_status == "healthy" and redis_status == "healthy"
    body = HealthResponse(
        status="ok" if all_healthy else "degraded",
        database=db_status,
        redis=redis_status,
    )
    return JSONResponse(
        content=body.model_dump(), status_code=200 if all_healthy else 503
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    tags=["health"],
)
async def health_detailed(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> JSONResponse:
    """Return detailed health with latency measurements. Requires authentication."""
    db_status, db_latency = await _check_db(db)
    redis_status, redis_latency = await _check_redis()

    all_healthy = db_status == "healthy" and redis_status == "healthy"
    body = DetailedHealthResponse(
        status="ok" if all_healthy else "degraded",
        database=DependencyDetail(status=db_status, latency_ms=db_latency),
        redis=DependencyDetail(status=redis_status, latency_ms=redis_latency),
        sentry_enabled=bool(settings.SENTRY_DSN),
        version=version("flowday-backend"),
    )
    return JSONResponse(
        content=body.model_dump(), status_code=200 if all_healthy else 503
    )
