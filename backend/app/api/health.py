from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.health import HealthResponse

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
