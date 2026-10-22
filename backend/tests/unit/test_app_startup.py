"""
Integration tests for FastAPI app startup and health endpoints.

Uses httpx.AsyncClient with ASGITransport — no real server needed.
Uses an in-memory SQLite database.
No real LLM, search, or content providers are invoked.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force test settings before importing the app
os.environ["LLM_PROVIDER"] = "fake"
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Clear settings cache if it was populated by other tests
from app.core import config as config_module

config_module.get_settings.cache_clear()


@pytest_asyncio.fixture()
async def client() -> AsyncClient:
    """Async test client with in-memory SQLite."""
    # Reset engine/session state for test isolation
    import app.db.session as session_module

    session_module._engine = None
    session_module._session_factory = None

    from app.main import create_app

    test_app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        # Trigger lifespan startup (creates tables)
        async with test_app.router.lifespan_context(test_app):
            yield ac


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_endpoint_has_request_id(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert "X-Request-ID" in resp.headers


@pytest.mark.asyncio
async def test_providers_health_fake_provider(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["llm"]["provider_name"] == "fake"
    assert data["llm"]["configured"] is True
    # API key must not appear anywhere in response
    assert "api_key" not in str(data)
    assert "secret" not in str(data).lower()


@pytest.mark.asyncio
async def test_smoke_test_blocked_without_flag(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/health/providers/smoke-test")
    assert resp.status_code == 429  # rate_limited when ALLOW_LIVE_SMOKE_TESTS=false


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_openapi_schema_loads(client: AsyncClient) -> None:
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "SupplyChain Sentinel"


@pytest.mark.asyncio
async def test_root_serves_frontend_when_dist_present(client: AsyncClient) -> None:
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "SupplyChain Sentinel" in resp.text
