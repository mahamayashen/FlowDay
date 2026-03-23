from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings
from app.core.database import dispose_engine, init_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of shared resources."""
    init_engine()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

    app = FastAPI(
        title="FlowDay API",
        description="AI-powered daily planner for freelancers",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router)

    return app


app = create_app()
