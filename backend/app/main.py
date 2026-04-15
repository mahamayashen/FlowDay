from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.core.config import settings
from app.core.database import dispose_engine, init_engine
from app.core.redis import close_redis, init_redis
from app.core.sentry import SentryBreadcrumbMiddleware, configure_sentry


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

    app.add_middleware(SentryBreadcrumbMiddleware)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)

    return app


app = create_app()
