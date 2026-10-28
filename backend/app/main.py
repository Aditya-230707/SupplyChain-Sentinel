"""
SupplyChain Sentinel — Production FastAPI application factory.

Wires together: settings, structured logging, database, CORS,
request-ID middleware, and API routers.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_investigations import router as investigations_router
from app.api.routes_reviews import router as reviews_router
from app.api.routes_suppliers import router as suppliers_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialise on startup, clean up on shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)
    log = structlog.get_logger("sentinel.startup")

    log.info(
        "sentinel_starting",
        env=settings.app_env,
        provider=settings.llm_provider,
        db_url=settings.database_url.split("///")[0] + "///***",  # redact path
    )

    await init_db()
    log.info("database_ready")

    yield

    log.info("sentinel_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SupplyChain Sentinel",
        description=(
            "Evidence-first supplier incident intelligence. "
            "Investigates public reports about supplier disruptions and compliance incidents."
        ),
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ---- CORS -----------------------------------------------
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    # ---- Request-ID middleware --------------------------------
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: object) -> Response:
        request_id = request.headers.get(settings.request_id_header, str(uuid.uuid4()))
        start = time.perf_counter()

        # Bind request ID for the duration of this request
        with structlog.contextvars.bound_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        ):
            response: Response = await call_next(request)  # type: ignore[arg-type]

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers[settings.request_id_header] = request_id
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
        return response

    # ---- Exception handlers ----------------------------------
    register_exception_handlers(app)

    # ---- Routers ---------------------------------------------
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(suppliers_router, prefix="/api/v1")
    app.include_router(investigations_router, prefix="/api/v1")
    app.include_router(reviews_router, prefix="/api/v1")

    # ---- Static Frontend Serving (Unified Hosting) ----------
    from pathlib import Path

    dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist_dir.exists() and (dist_dir / "index.html").exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app


app = create_app()
