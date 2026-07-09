"""FastAPI application factory.

Wires routers, exception handlers, and middleware. Domain errors raised by
services are translated into HTTP responses here so the service layer stays free
of transport concerns.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import dispose_engine
from app.core.errors import ConflictError, NotFoundError
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

# Baseline security headers applied to every response (spec §12).
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger.info("BrewIQ API starting", extra={"version": __version__})
    yield
    await dispose_engine()
    logger.info("BrewIQ API stopped")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title="BrewIQ API",
        version=__version__,
        description="Brewery discovery, extraction, scoring, and search.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.env != "production" else settings.cors_allow_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
