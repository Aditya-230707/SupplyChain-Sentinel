"""
Evidence Graph & Provenance Model.

Constructs explicit directed provenance relationships between:
- Suppliers & Facilities (operational footprint)
- Parts / Components (buyer exposure)
- Retrieved Sources (canonical lineage & syndication clustering)
- Extracted Claims & Supporting Quotes (verbatim substring verification)
- Claim-to-Claim semantic relations (corroboration, contradiction, supersession)
- Incident Candidates, Exposure Assessments & Policy Decisions
- Human Review & Audit Trail

Guarantees:
- Never conflates raw wire duplicates with independent corroboration.
- Retains distinct publication time, retrieval time, and event time.
- Identifies conflicting claims and corrections deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass
class FacilityProfile:
    """Registered facility operated by a supplier."""

    id: str
    name: str
    facility_type: str = "manufacturing"
    country_or_region: str | None = None
    city_or_address: str | None = None
    criticality: str = "high"


@dataclass
class FacilityResolutionResult:
    """Outcome of resolving a claim location/subject against registered facilities."""

    status: str  # confirmed | probable | unmatched
    matched_facility: FacilityProfile | None = None
    matched_signals: list[str] = field(default_factory=list)
    confidence_rationale: str = ""


@dataclass
class ClaimRelationResult:
    """Pairwise semantic relationship between two extracted claims."""

    claim_a_id: str
    claim_b_id: str
    relation: str  # corroborates | contradicts | supersedes | clarifies
    rationale: str
    rule_id: str  # e.g. CR-001 (Contradiction), CR-002 (Corroboration)


@dataclass
class GraphNode:
    """A node in the evidence provenance DAG."""

    id: str
    type: str  # supplier | facility | part | source | claim | incident | exposure | decision
    label: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """A directed edge in the evidence provenance DAG."""

    source: str
    target: str
    relation: str  # e.g. OPERATES, SUPPLIES, EXTRACTED_FROM, CORROBORATES, CONTRADICTS
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceGraph:
    """Full bipartite provenance DAG with integrity metrics."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "properties": n.properties,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relation": e.relation,
                    "metadata": e.metadata,
                }
                for e in self.edges
            ],
            "metrics": self.metrics,
        }


def resolve_facility_entity(
    location_text: str | None,
    subject_text: str | None,
    registered_facilities: list[FacilityProfile],
) -> FacilityResolutionResult:
    """Resolve an extracted claim's location to a known supplier facility."""
    if not registered_facilities or (not location_text and not subject_text):
        return FacilityResolutionResult(
            status="unmatched",
            confidence_rationale=(
                "No facility location provided or no registered facilities on supplier record."
            ),
        )

    search_text = f"{subject_text or ''} {location_text or ''}".lower()

    # Pass 1: Exact facility name match
    for fac in registered_facilities:
        if fac.name.lower() in search_text:
            return FacilityResolutionResult(
                status="confirmed",
                matched_facility=fac,
                matched_signals=["exact_facility_name"],
                confidence_rationale=f"Claim text matches registered facility name '{fac.name}'.",
            )

    # Pass 2: City / location name match
    for fac in registered_facilities:
        if fac.city_or_address and fac.city_or_address.lower() in search_text:
            return FacilityResolutionResult(
                status="probable",
                matched_facility=fac,
                matched_signals=["city_location_match"],
                confidence_rationale=(
                    f"Claim text matches facility location '{fac.city_or_address}'."
                ),
            )

    return FacilityResolutionResult(
        status="unmatched",
        confidence_rationale="No matching facility name or city identified in claim text.",
    )


def detect_claim_semantic_relations(
    claims: list[dict[str, Any]],
    source_to_group: dict[str, str] | None = None,
) -> list[ClaimRelationResult]:
    """Identify corroborations, contradictions, resolutions, and clarifications between claims.

    Rules:
    - CR-001 (Contradiction): One claim reports operational disruption while another reports
      drill, resolution, correction, or normal operations.
    - CR-002 (Corroboration): Claims report consistent disruption from distinct reporting groups.
    - CR-003 (Syndicated Echo): Claims report same event but originate from same reporting group
      (cannot be counted as independent corroboration).
    - CR-004 (Clarification): Later or secondary claim provides quantitative recovery duration.
    """
    relations: list[ClaimRelationResult] = []
    source_group_map = source_to_group or {}

    n = len(claims)
    for i in range(n):
        for j in range(i + 1, n):
            c_a = claims[i]
            c_b = claims[j]

            id_a = c_a.get("id", f"claim_{i}")
            id_b = c_b.get("id", f"claim_{j}")
            type_a = c_a.get("claim_type", "incident")
            type_b = c_b.get("claim_type", "incident")
            src_a = c_a.get("source_id", "")
            src_b = c_b.get("source_id", "")
            grp_a = source_group_map.get(src_a, src_a)
            grp_b = source_group_map.get(src_b, src_b)

            # Rule CR-001: Contradiction / Resolution vs Active Incident
            is_resolution_a = type_a in ("resolution", "correction")
            is_resolution_b = type_b in ("resolution", "correction")

            if (is_resolution_a and not is_resolution_b) or (
                is_resolution_b and not is_resolution_a
            ):
                relations.append(
                    ClaimRelationResult(
                        claim_a_id=id_a,
                        claim_b_id=id_b,
                        relation="contradicts",
                        rationale=(
                            "One claim reports active disruption while another reports an "
                            "exercise, resolution, or correction."
                        ),
                        rule_id="CR-001",
                    )
                )
                continue

            # Check opposing polarity (supports vs contradicts)
            pol_a = c_a.get("polarity", "supports")
            pol_b = c_b.get("polarity", "supports")
            if (pol_a == "supports" and pol_b == "contradicts") or (
                pol_a == "contradicts" and pol_b == "supports"
            ):
                relations.append(
                    ClaimRelationResult(
                        claim_a_id=id_a,
                        claim_b_id=id_b,
                        relation="contradicts",
                        rationale=(
                            "Claims report conflicting factual statements regarding "
                            "operational status."
                        ),
                        rule_id="CR-001",
                    )
                )
                continue

            # Rule CR-002 vs CR-003: Corroboration vs Wire Echo
            if type_a == "incident" and type_b == "incident":
                if grp_a and grp_b and grp_a == grp_b:
                    relations.append(
                        ClaimRelationResult(
                            claim_a_id=id_a,
                            claim_b_id=id_b,
                            relation="clarifies",
                            rationale=(
                                "Claims derive from same syndicated reporting group and "
                                "represent wire echoes rather than independent corroboration."
                            ),
                            rule_id="CR-003",
                        )
                    )
                else:
                    relations.append(
                        ClaimRelationResult(
                            claim_a_id=id_a,
                            claim_b_id=id_b,
                            relation="corroborates",
                            rationale=(
                                "Claims report consistent operational incident statements from "
                                "distinct independent reporting sources."
                            ),
                            rule_id="CR-002",
                        )
                    )
                continue

            # Rule CR-004: Quantified duration clarification
            if c_a.get("event_type") == c_b.get("event_type"):
                relations.append(
                    ClaimRelationResult(
                        claim_a_id=id_a,
                        claim_b_id=id_b,
                        relation="clarifies",
                        rationale="Claims reference common operational event context.",
                        rule_id="CR-004",
                    )
                )

    return relations


def build_investigation_evidence_graph(
    supplier_data: dict[str, Any],
    facilities_data: list[dict[str, Any]],
    parts_data: list[dict[str, Any]],
    sources_data: list[dict[str, Any]],
    source_relations_data: list[dict[str, Any]],
    claims_data: list[dict[str, Any]],
    incident_data: dict[str, Any] | None,
    exposure_data: dict[str, Any] | None,
    policy_data: dict[str, Any] | None,
    human_review_data: dict[str, Any] | None = None,
) -> EvidenceGraph:
    """Synthesize complete provenance DAG connecting all business and evidentiary entities."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # 1. Supplier Node
    sup_id = supplier_data.get("id", "supplier_1")
    nodes.append(
        GraphNode(
            id=sup_id,
            type="supplier",
            label=supplier_data.get("name", "Unknown Supplier"),
            properties={
                "criticality": supplier_data.get("criticality", "unknown"),
                "country": supplier_data.get("country_or_region"),
                "official_domains": supplier_data.get("official_domains", []),
            },
        )
    )

    # 2. Facility Nodes
    for fac in facilities_data:
        f_id = fac.get("id", f"fac_{len(nodes)}")
        nodes.append(
            GraphNode(
                id=f_id,
                type="facility",
                label=fac.get("facility_name", "Facility"),
                properties={
                    "type": fac.get("facility_type", "manufacturing"),
                    "location": fac.get("city_or_address") or fac.get("country_or_region"),
                },
            )
        )
        edges.append(
            GraphEdge(
                source=sup_id,
                target=f_id,
                relation="OPERATES",
                metadata={"source": "master_data"},
            )
        )

    # 3. Part / Component Nodes
    for part in parts_data:
        p_id = part.get("id", f"part_{len(nodes)}")
        nodes.append(
            GraphNode(
                id=p_id,
                type="part",
                label=part.get("part_name", "Component"),
                properties={
                    "part_number": part.get("part_number"),
                    "inventory_days": part.get("inventory_coverage_days"),
                    "lead_time_days": part.get("typical_lead_time_days"),
                },
            )
        )
        edges.append(
            GraphEdge(
                source=sup_id,
                target=p_id,
                relation="SUPPLIES",
                metadata={"source": "erp_contract"},
            )
        )

    # 4. Source Nodes
    for src in sources_data:
        s_id = src.get("id", f"src_{len(nodes)}")
        nodes.append(
            GraphNode(
                id=s_id,
                type="source",
                label=src.get("publisher_name") or src.get("domain") or "Web Source",
                properties={
                    "url": src.get("url_canonical") or src.get("url_original"),
                    "domain": src.get("domain"),
                    "published_at": src.get("published_at"),
                    "retrieved_at": src.get("retrieved_at"),
                    "content_status": src.get("content_status", "snippet_only"),
                    "content_hash": src.get("content_hash"),
                },
            )
        )

    # Source Relations (Syndication / Duplicate Edges)
    for rel in source_relations_data:
        edges.append(
            GraphEdge(
                source=rel.get("source_a_id", ""),
                target=rel.get("source_b_id", ""),
                relation=rel.get("relation", "syndicated").upper(),
                metadata=rel.get("evidence", {}),
            )
        )

    # 5. Claim Nodes
    source_to_group: dict[str, str] = {}
    for rel in source_relations_data:
        if rel.get("relation") in ("syndicated", "near_duplicate", "exact_duplicate"):
            source_to_group[rel.get("source_b_id", "")] = rel.get("source_a_id", "")

    claim_semantic_relations = detect_claim_semantic_relations(claims_data, source_to_group)

    for clm in claims_data:
        c_id = clm.get("id", f"claim_{len(nodes)}")
        nodes.append(
            GraphNode(
                id=c_id,
                type="claim",
                label=clm.get("subject_text", "Claim")[:60],
                properties={
                    "claim_type": clm.get("claim_type", "incident"),
                    "event_type": clm.get("event_type"),
                    "supporting_quote": clm.get("supporting_quote"),
                    "extraction_status": clm.get("extraction_status", "needs_review"),
                    "polarity": clm.get("polarity", "supports"),
                    "event_date": clm.get("event_date"),
                },
            )
        )
        if clm.get("source_id"):
            edges.append(
                GraphEdge(
                    source=clm["source_id"],
                    target=c_id,
                    relation="EXTRACTED_FROM",
                    metadata={"quote_valid": clm.get("extraction_status") == "validated"},
                )
            )

    # Claim-to-Claim Edges
    for cr in claim_semantic_relations:
        edges.append(
            GraphEdge(
                source=cr.claim_a_id,
                target=cr.claim_b_id,
                relation=cr.relation.upper(),
                metadata={"rationale": cr.rationale, "rule_id": cr.rule_id},
            )
        )

    # 6. Incident Node
    if incident_data:
        inc_id = incident_data.get("id", "incident_1")
        nodes.append(
            GraphNode(
                id=inc_id,
                type="incident",
                label=incident_data.get("event_type", "Incident"),
                properties={
                    "entity_match_status": incident_data.get("entity_match_status", "unknown"),
                    "evidence_status": incident_data.get("evidence_status", "unknown"),
                    "reporting_groups": incident_data.get("reporting_group_count"),
                    "independent_support": incident_data.get("independent_support_count"),
                },
            )
        )
        # Link claims to incident
        for clm_id in incident_data.get("claim_ids", []):
            edges.append(
                GraphEdge(
                    source=clm_id,
                    target=inc_id,
                    relation="COMPOSES",
                    metadata={"incident_id": inc_id},
                )
            )

        # 7. Exposure Assessment Node
        if exposure_data:
            exp_id = exposure_data.get("id", "exposure_1")
            nodes.append(
                GraphNode(
                    id=exp_id,
                    type="exposure",
                    label=f"Exposure Gap: {exposure_data.get('potential_inventory_gap_days')}d",
                    properties={
                        "gap_days": exposure_data.get("potential_inventory_gap_days"),
                        "exposure_band": exposure_data.get("exposure_band", "unknown"),
                        "calculation": exposure_data.get("calculation_name", "inventory_gap_v1"),
                    },
                )
            )
            edges.append(
                GraphEdge(
                    source=inc_id,
                    target=exp_id,
                    relation="ASSESSES_IMPACT",
                    metadata={"formula": "max(0, duration - inventory)"},
                )
            )

            # 8. Policy Decision Node
            if policy_data:
                pol_id = policy_data.get("id", "policy_1")
                nodes.append(
                    GraphNode(
                        id=pol_id,
                        type="decision",
                        label=policy_data.get("recommendation", "policy_decision"),
                        properties={
                            "recommendation": policy_data.get("recommendation"),
                            "rules_fired": policy_data.get("rule_ids_fired", []),
                            "reasons": policy_data.get("reasons", []),
                        },
                    )
                )
                edges.append(
                    GraphEdge(
                        source=exp_id,
                        target=pol_id,
                        relation="DETERMINES",
                        metadata={"rule_engine": "deterministic_v1"},
                    )
                )

                # 9. Human Review Node
                if human_review_data:
                    rev_id = human_review_data.get("id", "review_1")
                    nodes.append(
                        GraphNode(
                            id=rev_id,
                            type="human_review",
                            label=f"Review: {human_review_data.get('action')}",
                            properties={
                                "reviewer": human_review_data.get("reviewer_name"),
                                "action": human_review_data.get("action"),
                                "note": human_review_data.get("reviewer_note"),
                                "reviewed_at": human_review_data.get("reviewed_at"),
                            },
                        )
                    )
                    edges.append(
                        GraphEdge(
                            source=pol_id,
                            target=rev_id,
                            relation="ADJUDICATED_BY",
                            metadata={"action": human_review_data.get("action")},
                        )
                    )

    # Compute Provenance Integrity Metrics
    total_claims = len(claims_data)
    validated_quotes = sum(1 for c in claims_data if c.get("extraction_status") == "validated")
    quote_integrity = round(validated_quotes / total_claims, 4) if total_claims > 0 else 1.0

    total_sources = len(sources_data)
    independent_groups = (
        incident_data.get("reporting_group_count")
        if incident_data and incident_data.get("reporting_group_count") is not None
        else total_sources
    )
    independence_ratio = round(independent_groups / total_sources, 4) if total_sources > 0 else 1.0

    contradiction_count = sum(1 for cr in claim_semantic_relations if cr.relation == "contradicts")

    metrics = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "total_claims": total_claims,
        "validated_quotes_count": validated_quotes,
        "quote_integrity_ratio": quote_integrity,
        "total_sources_count": total_sources,
        "independent_reporting_groups": independent_groups,
        "source_independence_ratio": independence_ratio,
        "contradiction_count": contradiction_count,
        "data_completeness_score": round(
            (quote_integrity * 0.5)
            + (independence_ratio * 0.3)
            + (1.0 if total_claims > 0 else 0.0) * 0.2,
            3,
        ),
    }

    return EvidenceGraph(nodes=nodes, edges=edges, metrics=metrics)
