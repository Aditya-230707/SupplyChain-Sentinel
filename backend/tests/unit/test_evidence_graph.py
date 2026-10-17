"""
Unit tests for Evidence Graph, Provenance Model, and Claim Relations.

Covers:
- Facility entity resolution (exact name, city/address match, unmatched)
- Semantic claim relationship detection (contradiction, corroboration, wire echo)
- Evidence DAG construction and provenance metrics calculation
- Integration with investigation pipeline and graph endpoint
"""

from __future__ import annotations

import pytest

from app.pipeline.evidence_graph import (
    FacilityProfile,
    build_investigation_evidence_graph,
    detect_claim_semantic_relations,
    resolve_facility_entity,
)


def test_facility_entity_resolution_exact_name() -> None:
    facs = [
        FacilityProfile(
            id="fac_1",
            name="Apex Dresden Fab 1",
            facility_type="manufacturing",
            country_or_region="Germany",
            city_or_address="Dresden",
        )
    ]
    res = resolve_facility_entity(
        location_text="Saxony",
        subject_text="Apex Dresden Fab 1 cleanroom explosion",
        registered_facilities=facs,
    )
    assert res.status == "confirmed"
    assert res.matched_facility is not None
    assert res.matched_facility.id == "fac_1"
    assert "exact_facility_name" in res.matched_signals


def test_facility_entity_resolution_city_match() -> None:
    facs = [
        FacilityProfile(
            id="fac_2",
            name="Titan North Substation",
            facility_type="substation",
            country_or_region="USA",
            city_or_address="Austin, TX",
        )
    ]
    res = resolve_facility_entity(
        location_text="Austin, TX plant",
        subject_text="Titan facility transformer failure",
        registered_facilities=facs,
    )
    assert res.status == "probable"
    assert res.matched_facility is not None
    assert res.matched_facility.id == "fac_2"


def test_facility_entity_resolution_unmatched() -> None:
    facs = [
        FacilityProfile(
            id="fac_1",
            name="Apex Dresden Fab 1",
            facility_type="manufacturing",
            country_or_region="Germany",
            city_or_address="Dresden",
        )
    ]
    res = resolve_facility_entity(
        location_text="Tokyo, Japan",
        subject_text="Facility inspection conducted",
        registered_facilities=facs,
    )
    assert res.status == "unmatched"
    assert res.matched_facility is None


def test_claim_relation_contradiction_active_disruption_vs_drill() -> None:
    claims = [
        {
            "id": "c1",
            "claim_type": "incident",
            "event_type": "operational_disruption",
            "source_id": "s1",
            "polarity": "supports",
        },
        {
            "id": "c2",
            "claim_type": "resolution",
            "event_type": "operational_disruption",
            "source_id": "s2",
            "polarity": "supports",
        },
    ]
    rels = detect_claim_semantic_relations(claims)
    assert len(rels) == 1
    assert rels[0].relation == "contradicts"
    assert rels[0].rule_id == "CR-001"


def test_claim_relation_independent_corroboration() -> None:
    claims = [
        {
            "id": "c1",
            "claim_type": "incident",
            "event_type": "operational_disruption",
            "source_id": "s1",
            "polarity": "supports",
        },
        {
            "id": "c2",
            "claim_type": "incident",
            "event_type": "operational_disruption",
            "source_id": "s2",
            "polarity": "supports",
        },
    ]
    source_to_group = {"s1": "group_1", "s2": "group_2"}
    rels = detect_claim_semantic_relations(claims, source_to_group)
    assert len(rels) == 1
    assert rels[0].relation == "corroborates"
    assert rels[0].rule_id == "CR-002"


def test_claim_relation_syndicated_wire_echo_not_independent() -> None:
    claims = [
        {
            "id": "c1",
            "claim_type": "incident",
            "event_type": "operational_disruption",
            "source_id": "s1",
            "polarity": "supports",
        },
        {
            "id": "c2",
            "claim_type": "incident",
            "event_type": "operational_disruption",
            "source_id": "s2",
            "polarity": "supports",
        },
    ]
    # Both sources belong to the same wire syndication group
    source_to_group = {"s1": "reuters_wire_grp", "s2": "reuters_wire_grp"}
    rels = detect_claim_semantic_relations(claims, source_to_group)
    assert len(rels) == 1
    assert rels[0].relation == "clarifies"
    assert rels[0].rule_id == "CR-003"
    assert "syndicated" in rels[0].rationale


def test_build_investigation_evidence_graph_structure_and_metrics() -> None:
    supplier = {
        "id": "sup_1",
        "name": "Apex Semiconductor",
        "criticality": "high",
        "country_or_region": "Germany",
        "official_domains": ["apex-semi.de"],
    }
    facilities = [
        {"id": "fac_1", "facility_name": "Dresden Fab 1", "facility_type": "manufacturing"}
    ]
    parts = [
        {
            "id": "part_1",
            "part_name": "MCU-100",
            "inventory_coverage_days": 14.0,
            "typical_lead_time_days": 45.0,
        }
    ]
    sources = [
        {
            "id": "s1",
            "url_canonical": "https://reuters.com/news1",
            "publisher_name": "Reuters",
            "domain": "reuters.com",
            "retrieved_at": "2026-10-17T12:00:00Z",
            "content_status": "available",
            "content_hash": "hash123",
        }
    ]
    source_relations = []
    claims = [
        {
            "id": "c1",
            "subject_text": "Apex Semiconductor Fab 1",
            "source_id": "s1",
            "claim_type": "incident",
            "event_type": "operational_disruption",
            "supporting_quote": "Fab 1 experienced a major fire",
            "extraction_status": "validated",
            "polarity": "supports",
            "event_date": "2026-10-15",
        }
    ]
    incident = {
        "id": "inc_1",
        "event_type": "operational_disruption",
        "entity_match_status": "confirmed",
        "evidence_status": "single_source",
        "reporting_group_count": 1,
        "independent_support_count": 1,
        "claim_ids": ["c1"],
    }
    exposure = {
        "id": "exp_1",
        "potential_inventory_gap_days": 16.0,
        "exposure_band": "high",
        "calculation_name": "inventory_gap_v1",
    }
    policy = {
        "id": "pol_1",
        "recommendation": "urgent_human_review",
        "rule_ids_fired": ["P-001"],
        "reasons": ["Severe inventory gap on critical component."],
    }

    graph = build_investigation_evidence_graph(
        supplier_data=supplier,
        facilities_data=facilities,
        parts_data=parts,
        sources_data=sources,
        source_relations_data=source_relations,
        claims_data=claims,
        incident_data=incident,
        exposure_data=exposure,
        policy_data=policy,
    )

    g_dict = graph.to_dict()
    assert "nodes" in g_dict
    assert "edges" in g_dict
    assert "metrics" in g_dict

    node_types = {n["type"] for n in g_dict["nodes"]}
    assert "supplier" in node_types
    assert "facility" in node_types
    assert "part" in node_types
    assert "source" in node_types
    assert "claim" in node_types
    assert "incident" in node_types
    assert "exposure" in node_types
    assert "decision" in node_types

    metrics = g_dict["metrics"]
    assert metrics["quote_integrity_ratio"] == 1.0
    assert metrics["total_claims"] == 1
    assert metrics["validated_quotes_count"] == 1
    assert metrics["contradiction_count"] == 0
    assert metrics["data_completeness_score"] > 0.0


@pytest.fixture
async def client():
    from httpx import ASGITransport, AsyncClient

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
async def test_evidence_graph_api_endpoint(client) -> None:
    # 1. Create a supplier
    sup_resp = await client.post(
        "/api/v1/suppliers",
        json={
            "name": "Graph Test Semiconductor AG",
            "aliases": ["GTS"],
            "country_or_region": "Germany",
            "criticality": "high",
        },
    )
    assert sup_resp.status_code == 201
    sup_id = sup_resp.json()["id"]

    # 2. Run fixture investigation
    inv_resp = await client.post(
        "/api/v1/investigations",
        json={"supplier_id": sup_id, "search_mode": "fixture"},
    )
    assert inv_resp.status_code == 201
    inv_id = inv_resp.json()["id"]

    # 3. Fetch evidence graph
    graph_resp = await client.get(f"/api/v1/investigations/{inv_id}/graph")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()

    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "metrics" in graph_data
    assert graph_data["metrics"]["total_sources_count"] >= 1
    assert graph_data["metrics"]["quote_integrity_ratio"] == 1.0
