from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.schedule_blocks import router as schedule_blocks_router
from app.api.sync import router as sync_router
from app.api.tasks import router as tasks_router
from app.api.time_entries import router as time_entries_router
from app.core.config import settings
from app.core.database import dispose_engine, init_engine
from app.core.metrics import configure_metrics
from app.core.redis import close_redis, init_redis
from app.core.sentry import SentryBreadcrumbMiddleware, configure_sentry
from app.services import google_calendar_provider as _gcal_provider  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of shared resources."""
    init_engine()
    try:
        await init_redis(settings.REDIS_URL)
    except Exception:
        await dispose_engine()
        raise
    yield
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_sentry(settings.SENTRY_DSN)

    app = FastAPI(
        title="FlowDay API",
        description="AI-powered daily planner for freelancers",
        version="0.1.0",
        lifespan=lifespan,
    )

    configure_metrics(app, enabled=settings.PROMETHEUS_ENABLED)
    app.add_middleware(SentryBreadcrumbMiddleware)  # type: ignore[arg-type]

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(analytics_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)
    app.include_router(schedule_blocks_router)
    app.include_router(sync_router)
    app.include_router(time_entries_router)

    return app


app = create_app()
