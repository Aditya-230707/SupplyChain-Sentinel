"""
Health and provider status endpoints.

GET  /api/v1/health          — app + db status
GET  /api/v1/health/providers — provider configured/reachable state (no keys)
POST /api/v1/health/providers/smoke-test — live provider call (requires ALLOW_LIVE_SMOKE_TESTS=true)
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import RateLimitError
from app.db.session import get_session_factory

log = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


class DBStatus(BaseModel):
    ok: bool
    error: str | None = None


class AppHealth(BaseModel):
    status: str  # ok | degraded | error
    version: str
    environment: str
    timestamp: str
    database: DBStatus


class ProviderHealth(BaseModel):
    provider_name: str
    model_id: str | None = None
    configured: bool
    reachable: bool | None  # None = not yet checked
    model_available: bool | None = None
    error: str | None = None


class ProvidersHealthResponse(BaseModel):
    llm: ProviderHealth
    search: ProviderHealth | None = None
    content: ProviderHealth | None = None


@router.get("/health", response_model=AppHealth)
async def health(settings: Settings = Depends(get_settings)) -> AppHealth:
    """Return application and database health."""
    db_ok = False
    db_error: str | None = None

    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = type(exc).__name__

    overall = "ok" if db_ok else "degraded"

    return AppHealth(
        status=overall,
        version="0.1.0",
        environment=settings.app_env,
        timestamp=datetime.now(UTC).isoformat(),
        database=DBStatus(ok=db_ok, error=db_error),
    )


@router.get("/health/providers", response_model=ProvidersHealthResponse)
async def providers_health(settings: Settings = Depends(get_settings)) -> ProvidersHealthResponse:
    """Return provider configuration status. Never exposes API keys."""
    from app.providers.factory import get_llm_provider

    llm_provider = get_llm_provider()
    # For health check, we only report configured state without making network calls
    llm_health = ProviderHealth(
        provider_name=llm_provider.provider_name,
        model_id=llm_provider.model_id,
        configured=True,
        reachable=None,  # Not checked unless smoke test is called
    )

    search_health: ProviderHealth | None = None
    if settings.tavily_api_key:
        search_health = ProviderHealth(
            provider_name="tavily_search",
            configured=True,
            reachable=None,
        )
    else:
        search_health = ProviderHealth(
            provider_name="duckduckgo_search",
            configured=True,
            reachable=None,
        )

    return ProvidersHealthResponse(llm=llm_health, search=search_health)


@router.post("/health/providers/smoke-test")
async def providers_smoke_test(
    settings: Settings = Depends(get_settings),
) -> dict:
    """Run a live provider health check.

    Requires ALLOW_LIVE_SMOKE_TESTS=true. Makes a real API call.
    Dev/admin use only — do not expose publicly without authentication.
    """
    if not settings.allow_live_smoke_tests:
        raise RateLimitError(
            "Live smoke tests are disabled. Set ALLOW_LIVE_SMOKE_TESTS=true in .env to enable."
        )

    from app.providers.factory import get_llm_provider

    llm_provider = get_llm_provider()
    result = await llm_provider.health_check()

    log.info(
        "smoke_test_completed", provider=result.get("provider_name"), status=result.get("error")
    )
    # Never return the full result dict — filter to safe fields
    return {
        "provider_name": result.get("provider_name"),
        "model_id": result.get("model_id"),
        "configured": result.get("configured"),
        "reachable": result.get("reachable"),
        "model_available": result.get("model_available"),
        "error": result.get("error"),
    }
