"""
Tests for Phase 3 user workflows, human decision gate, and search mode handling.

Covers:
- Investigation creation with search_mode="fixture" (default) vs search_mode="live".
- Mandatory failure when live search is requested without TAVILY_API_KEY (no silent fallback).
- Human decision recording (accepting recommendation).
- Human decision override/rejection (requires non-empty reviewer note).
- Audit trail persistence and immutability (original recommendation unchanged).
- Listing of incidents, investigations, source relations, and audit events.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import (
    AuditEvent as AuditEventModel,
)
from app.db.models import (
    IncidentCandidate as IncidentCandidateModel,
)
from app.db.models import (
    InvestigationRun as InvestigationRunModel,
)
from app.db.models import (
    PolicyDecision as PolicyDecisionModel,
)
from app.db.models import (
    Supplier as SupplierModel,
)
from app.db.models import (
    SupplierPart as SupplierPartModel,
)
from app.db.session import get_db_session
from app.main import app
from app.providers.fake_provider import FakeLLMProvider
from app.schemas.claim import ClaimExtractionResponse, ExtractedClaimItem


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_live_search_without_key_raises_error_no_silent_fallback(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    """If search_mode='live' is requested and TAVILY_API_KEY is unset, it must fail explicitly."""
    monkeypatch.setenv("TAVILY_API_KEY", "")

    supplier = SupplierModel(name="TechCorp Sensors Ltd", country_or_region="Germany")
    db_session.add(supplier)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/investigations",
        json={"supplier_id": supplier.id, "search_mode": "live"},
    )
    assert resp.status_code == 502
    err_body = resp.json()
    assert "TAVILY_API_KEY is not configured" in err_body["error"]["message"]


@pytest.mark.asyncio
async def test_fixture_search_mode_runs_cleanly(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    """Default search_mode='fixture' uses the demo scenario and completes an investigation."""
    supplier = SupplierModel(
        name="Silicon Foundry Dresden GmbH",
        country_or_region="Germany",
        official_domains=["silicon-dresden.de"],
    )
    db_session.add(supplier)
    await db_session.flush()

    part = SupplierPartModel(
        supplier_id=supplier.id,
        part_name="Automotive Microcontroller",
        part_number="MICRO-01",
        inventory_coverage_days="14",
        recovery_duration_days="45",
    )
    db_session.add(part)
    await db_session.commit()

    # Provide fake LLM provider matching fixture output
    llm_resp = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="Silicon Foundry Dresden GmbH",
                event_type="operational_disruption",
                object_text="Cleanroom fire halting wafer production for 45 days",
                claim_type="incident",
                polarity="supports",
                supporting_quote=(
                    "Silicon Foundry Dresden GmbH experienced a severe cleanroom fire on Tuesday."
                ),
            )
        ]
    )
    fake_llm = FakeLLMProvider(responses=[llm_resp, llm_resp, llm_resp])
    monkeypatch.setattr("app.api.routes_investigations.get_llm_provider", lambda: fake_llm)

    resp = await client.post(
        "/api/v1/investigations",
        json={"supplier_id": supplier.id, "search_mode": "fixture"},
    )
    assert resp.status_code == 201
    run_id = resp.json()["id"]

    # Verify sources and relations
    sources_resp = await client.get(f"/api/v1/investigations/{run_id}/sources")
    assert sources_resp.status_code == 200
    sources = sources_resp.json()
    assert len(sources) >= 2

    relations_resp = await client.get(f"/api/v1/investigations/{run_id}/relations")
    assert relations_resp.status_code == 200

    # Verify incidents endpoint
    incidents_resp = await client.get(f"/api/v1/investigations/{run_id}/incidents")
    assert incidents_resp.status_code == 200
    incidents = incidents_resp.json()
    assert len(incidents) >= 1
    assert incidents[0]["policy_decision"] is not None


@pytest.mark.asyncio
async def test_human_decision_approve_recommendation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    supplier = SupplierModel(name="Test Fab Corp", country_or_region="Germany")
    db_session.add(supplier)
    await db_session.flush()

    run = InvestigationRunModel(supplier_id=supplier.id, status="completed")
    db_session.add(run)
    await db_session.flush()

    incident = IncidentCandidateModel(
        investigation_id=run.id,
        event_type="operational_disruption",
        review_required=True,
    )
    db_session.add(incident)
    await db_session.flush()

    policy_dec = PolicyDecisionModel(
        incident_id=incident.id,
        policy_version="1.0",
        recommendation="urgent_human_review",
        reasons=["Calculated inventory gap of 31 days."],
        blockers=[],
        human_review_required=True,
    )
    db_session.add(policy_dec)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/incidents/{incident.id}/decision",
        json={
            "action": "approve_recommendation",
            "reviewer_name": "Senior Sourcing Lead",
            "reviewer_note": "Acknowledged. Triggering alternate supplier allocation.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["action"] == "approve_recommendation"
    assert data["prior_recommendation"] == "urgent_human_review"

    # Verify incident review_required updated to False
    updated_incident = await db_session.get(IncidentCandidateModel, incident.id)
    assert updated_incident.review_required is False

    # Original policy recommendation must NOT be mutated
    reloaded_policy = await db_session.get(PolicyDecisionModel, policy_dec.id)
    assert reloaded_policy.recommendation == "urgent_human_review"

    # Verify audit event was logged
    audit_events = (
        (
            await db_session.execute(
                select(AuditEventModel).where(AuditEventModel.entity_id == incident.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_events) == 1
    assert audit_events[0].event_type == "human_disposition"


@pytest.mark.asyncio
async def test_human_decision_override_requires_rationale(
    client: AsyncClient,
    db_session: AsyncSession,
):
    supplier = SupplierModel(name="Test Fab Corp 2", country_or_region="Germany")
    db_session.add(supplier)
    await db_session.flush()

    run = InvestigationRunModel(supplier_id=supplier.id, status="completed")
    db_session.add(run)
    await db_session.flush()

    incident = IncidentCandidateModel(
        investigation_id=run.id,
        event_type="operational_disruption",
        review_required=True,
    )
    db_session.add(incident)
    await db_session.flush()

    policy_dec = PolicyDecisionModel(
        incident_id=incident.id,
        policy_version="1.0",
        recommendation="urgent_human_review",
        reasons=["Risk detected."],
    )
    db_session.add(policy_dec)
    await db_session.commit()

    # Rejection without note -> 422
    resp_empty = await client.post(
        f"/api/v1/incidents/{incident.id}/decision",
        json={"action": "reject_recommendation", "reviewer_note": ""},
    )
    assert resp_empty.status_code == 422
    assert "rationale" in resp_empty.json()["error"]["message"].lower()

    # Rejection with note -> succeeds
    resp_with_note = await client.post(
        f"/api/v1/incidents/{incident.id}/decision",
        json={
            "action": "reject_recommendation",
            "override_recommendation": "monitor",
            "reviewer_note": "Verified with plant director: backup cleanroom is active.",
        },
    )
    assert resp_with_note.status_code == 201
    assert resp_with_note.json()["action"] == "reject_recommendation"
    assert resp_with_note.json()["override_recommendation"] == "monitor"

    # Verify reviews endpoint
    reviews_resp = await client.get(f"/api/v1/incidents/{incident.id}/reviews")
    assert reviews_resp.status_code == 200
    assert len(reviews_resp.json()) == 1


@pytest.mark.asyncio
async def test_audit_events_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET /api/v1/audit-events returns logged events."""
    event = AuditEventModel(
        event_type="human_disposition",
        entity_type="incident_candidate",
        entity_id="inc-123",
        data={"note": "Approved"},
    )
    db_session.add(event)
    await db_session.commit()

    resp = await client.get("/api/v1/audit-events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "human_disposition"
