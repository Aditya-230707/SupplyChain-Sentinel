"""Unit tests for Bounded Next-Best-Investigation Loop."""

from __future__ import annotations

from app.pipeline.investigation_loop import (
    EvidenceGap,
    StepTraceRecord,
    generate_candidate_investigations,
    identify_evidence_gaps,
    rank_investigation_candidates,
)


def test_identify_evidence_gaps_all_present():
    gaps = identify_evidence_gaps(
        supplier_name="Apex Photonics",
        entity_status="ambiguous",
        evidence_status="single_source",
        reporting_group_count=1,
        has_duration=False,
        has_contradictions=True,
        facility_matched=False,
    )

    gap_types = [g.gap_type for g in gaps]
    assert "ambiguous_identity" in gap_types
    assert "conflicting_claims" in gap_types
    assert "missing_duration" in gap_types
    assert "single_unverified_source" in gap_types
    assert "facility_unresolved" in gap_types
    assert len(gaps) == 5


def test_identify_evidence_gaps_none_when_complete():
    gaps = identify_evidence_gaps(
        supplier_name="Apex Photonics",
        entity_status="confirmed",
        evidence_status="corroborated",
        reporting_group_count=3,
        has_duration=True,
        has_contradictions=False,
        facility_matched=True,
    )
    assert len(gaps) == 0


def test_generate_candidate_investigations():
    gaps = [
        EvidenceGap("missing_duration", "Need duration", "Apex", 0.8),
        EvidenceGap("facility_unresolved", "Need plant", "Apex", 0.6),
    ]
    candidates = generate_candidate_investigations(
        supplier_name="Apex Photonics",
        gaps=gaps,
        executed_queries=['"Apex Photonics" restart timeline recovery weeks duration operational'],
    )
    # The first candidate was already executed, so only the facility candidate should remain
    assert len(candidates) == 1
    assert candidates[0].targeted_gap == "facility_unresolved"
    assert "manufacturing plant" in candidates[0].query


def test_rank_investigation_candidates_ordering():
    gaps = [
        EvidenceGap("missing_duration", "No duration", "Apex", 0.8),
        EvidenceGap("facility_unresolved", "No plant", "Apex", 0.6),
    ]
    executed = ['"Apex Photonics" incident disruption']
    candidates = generate_candidate_investigations("Apex Photonics", gaps, executed)
    ranked = rank_investigation_candidates(candidates, gaps, executed)

    assert len(ranked) == 2
    # missing_duration has higher impact (0.8 vs 0.6) and higher relevance (0.90 vs 0.75)
    assert ranked[0].targeted_gap == "missing_duration"
    assert ranked[0].heuristic_score > ranked[1].heuristic_score
    assert "total_heuristic_voi" in ranked[0].ranking_details
    assert ranked[0].ranking_details["total_heuristic_voi"] == ranked[0].heuristic_score


def test_step_trace_record_to_dict():
    record = StepTraceRecord(
        step_number=1,
        query="test query",
        targeted_gap="missing_duration",
        rationale="test rationale",
        heuristic_score=0.78,
        new_sources_count=2,
        new_claims_count=3,
        prior_recommendation="monitor",
        new_recommendation="request_supplier_confirmation",
        recommendation_changed=True,
        termination_reason="budget_exhausted",
    )
    d = record.to_dict()
    assert d["step_number"] == 1
    assert d["recommendation_changed"] is True
    assert d["new_sources_count"] == 2
    assert d["termination_reason"] == "budget_exhausted"
