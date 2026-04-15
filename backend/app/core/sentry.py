from __future__ import annotations

import sentry_sdk
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


def configure_sentry(dsn: str | None) -> None:
    """Initialise Sentry if a DSN is provided; silently skip otherwise."""
    if not dsn:
        return
    sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)


class SentryBreadcrumbMiddleware(BaseHTTPMiddleware):
    """Add a Sentry breadcrumb for every incoming HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        sentry_sdk.add_breadcrumb(
            category="http",
            message=f"{request.method} {request.url.path}",
            level="info",
        )
        response = await call_next(request)
        return response
