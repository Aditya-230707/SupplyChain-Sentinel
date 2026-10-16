"""
Integration tests for Supplier API endpoints.

Uses in-memory SQLite and ASGI test client.
No real LLM or external providers.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["LLM_PROVIDER"] = "fake"
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.core import config as config_module

config_module.get_settings.cache_clear()


@pytest_asyncio.fixture()
async def client() -> AsyncClient:
    import app.db.session as session_module

    session_module._engine = None
    session_module._session_factory = None

    from app.main import create_app

    test_app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        async with test_app.router.lifespan_context(test_app):
            yield ac


@pytest.mark.asyncio
async def test_create_supplier_minimal(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/suppliers", json={"name": "Acme Corp"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme Corp"
    assert data["criticality"] == "unknown"
    assert data["active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_supplier_with_parts(client: AsyncClient) -> None:
    payload = {
        "name": "Test Supplier",
        "criticality": "high",
        "parts": [
            {
                "part_name": "Widget A",
                "inventory_coverage_days": "30.5",
                "alternative_supplier_available": "no",
            }
        ],
    }
    resp = await client.post("/api/v1/suppliers", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["parts"]) == 1
    assert data["parts"][0]["inventory_coverage_days"] == "30.5"
    assert data["parts"][0]["alternative_supplier_available"] == "no"


@pytest.mark.asyncio
async def test_create_supplier_null_inventory_preserved(client: AsyncClient) -> None:
    """Null inventory_coverage_days must remain null — not become 0."""
    resp = await client.post(
        "/api/v1/suppliers",
        json={
            "name": "Null Inventory Supplier",
            "parts": [{"part_name": "Part X", "inventory_coverage_days": None}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["parts"][0]["inventory_coverage_days"] is None


@pytest.mark.asyncio
async def test_create_supplier_invalid_criticality(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/suppliers",
        json={"name": "Acme", "criticality": "extreme"},
    )
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "request_invalid"


@pytest.mark.asyncio
async def test_list_suppliers_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/suppliers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_suppliers_after_create(client: AsyncClient) -> None:
    await client.post("/api/v1/suppliers", json={"name": "Supplier Alpha"})
    await client.post("/api/v1/suppliers", json={"name": "Supplier Beta"})

    resp = await client.get("/api/v1/suppliers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    names = [s["name"] for s in data["items"]]
    assert "Supplier Alpha" in names
    assert "Supplier Beta" in names


@pytest.mark.asyncio
async def test_get_supplier_by_id(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/suppliers", json={"name": "Lookup Supplier"})
    supplier_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/suppliers/{supplier_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Lookup Supplier"


@pytest.mark.asyncio
async def test_get_supplier_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/suppliers/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_patch_supplier_name(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/suppliers", json={"name": "Old Name"})
    supplier_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/suppliers/{supplier_id}",
        json={"name": "New Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_supplier_query_filter(client: AsyncClient) -> None:
    await client.post("/api/v1/suppliers", json={"name": "MatchMe Corp"})
    await client.post("/api/v1/suppliers", json={"name": "NoMatch Ltd"})

    resp = await client.get("/api/v1/suppliers?query=MatchMe")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "MatchMe Corp"
