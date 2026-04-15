from __future__ import annotations

import time

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

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return application health status including DB and Redis connectivity."""
    db_status = "healthy"
    redis_status = "healthy"
    all_healthy = True

    # Check database
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
        all_healthy = False

    # Check Redis
    try:
        redis = get_redis()
        await redis.ping()
    except Exception:
        redis_status = "unhealthy"
        all_healthy = False

    status_code = 200 if all_healthy else 503
    body = HealthResponse(
        status="ok" if all_healthy else "degraded",
        database=db_status,
        redis=redis_status,
    )
    return JSONResponse(content=body.model_dump(), status_code=status_code)


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
    all_healthy = True

    # Check database with latency
    db_status = "healthy"
    start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
        all_healthy = False
    db_latency = round((time.monotonic() - start) * 1000, 2)

    # Check Redis with latency
    redis_status = "healthy"
    start = time.monotonic()
    try:
        redis = get_redis()
        await redis.ping()
    except Exception:
        redis_status = "unhealthy"
        all_healthy = False
    redis_latency = round((time.monotonic() - start) * 1000, 2)

    body = DetailedHealthResponse(
        status="ok" if all_healthy else "degraded",
        database=DependencyDetail(status=db_status, latency_ms=db_latency),
        redis=DependencyDetail(status=redis_status, latency_ms=redis_latency),
        sentry_enabled=bool(settings.SENTRY_DSN),
        version="0.1.0",
    )
    return JSONResponse(content=body.model_dump(), status_code=200 if all_healthy else 503)
