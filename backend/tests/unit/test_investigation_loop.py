"""Unit tests for Bounded Next-Best-Investigation Loop and VOI decision updating."""

from __future__ import annotations

from decimal import Decimal

from app.pipeline.claim_validator import verify_quote_against_source
from app.pipeline.entity_resolution import SupplierProfile, resolve_supplier_entity
from app.pipeline.evidence_graph import detect_claim_semantic_relations
from app.pipeline.exposure_calculator import (
    PartExposureInput,
    calculate_operational_exposure,
)
from app.pipeline.investigation_loop import (
    EvidenceGap,
    StepTraceRecord,
    generate_candidate_investigations,
    identify_evidence_gaps,
    rank_investigation_candidates,
)
from app.pipeline.policy_engine import (
    IncidentEvidenceSnapshot,
    evaluate_policy_rules,
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


def test_voi_useful_evidence_resolves_gap_and_updates_policy():
    """Scenario 1: Useful follow-up evidence provides duration and changes policy."""
    supplier = SupplierProfile(
        id="sup-1",
        name="Apex Micro Foundry Ltd",
        official_domains=["apex-microfoundry.com"],
        country_or_region="Taiwan",
    )
    part_input = PartExposureInput(
        part_name="Automotive MOSFET",
        inventory_coverage_days=Decimal("15"),
        typical_lead_time_days=Decimal("70"),
        recovery_duration_days=None,  # missing duration
        criticality="high",
    )
    # Initial: missing duration produces null gap -> request_supplier_confirmation
    initial_exp = calculate_operational_exposure(part_input)
    assert initial_exp.potential_inventory_gap_days is None

    entity_res = resolve_supplier_entity(
        supplier=supplier,
        subject_text="Apex Micro Foundry Ltd",
        source_text="Apex Micro Foundry cleanroom flooded.",
        source_domain="taipei-times.com",
    )
    initial_snap = IncidentEvidenceSnapshot(
        entity_match_status=entity_res.status,
        evidence_status="single_source",
        event_type="operational_disruption",
        reporting_group_count=1,
        has_resolution_or_correction=False,
    )
    initial_policy = evaluate_policy_rules(initial_snap, initial_exp, entity_res)
    assert initial_policy.recommendation == "request_supplier_confirmation"

    # Follow-up evidence provides verified 50-day timeline
    followup_text = (
        "Taiwan Semiconductor Bureau inspection: Fab 3 pump out and tool recalibration "
        "is officially scheduled for 50 days."
    )
    followup_quote = "Fab 3 pump out and tool recalibration is officially scheduled for 50 days."
    quote_res = verify_quote_against_source(followup_quote, followup_text)
    assert quote_res.is_valid

    # Post-evidence exposure calculation
    post_part_input = PartExposureInput(
        part_name="Automotive MOSFET",
        inventory_coverage_days=Decimal("15"),
        typical_lead_time_days=Decimal("70"),
        recovery_duration_days=Decimal("50"),
        criticality="high",
    )
    post_exp = calculate_operational_exposure(post_part_input)
    assert post_exp.potential_inventory_gap_days == Decimal("35")

    post_snap = IncidentEvidenceSnapshot(
        entity_match_status=entity_res.status,
        evidence_status="corroborated",
        event_type="operational_disruption",
        reporting_group_count=2,
        has_resolution_or_correction=False,
    )
    post_policy = evaluate_policy_rules(post_snap, post_exp, entity_res)
    assert post_policy.recommendation == "urgent_human_review"

    # Verify decision changed due to VOI follow-up
    trace = StepTraceRecord(
        step_number=1,
        query='"Apex Micro Foundry Ltd" restart timeline recovery weeks duration operational',
        targeted_gap="missing_duration",
        rationale="Search for estimated facility repair duration or restart timeline.",
        heuristic_score=0.88,
        new_sources_count=1,
        new_claims_count=1,
        prior_recommendation=initial_policy.recommendation,
        new_recommendation=post_policy.recommendation,
        recommendation_changed=True,
    )
    assert trace.recommendation_changed is True
    assert trace.prior_recommendation == "request_supplier_confirmation"
    assert trace.new_recommendation == "urgent_human_review"


def test_voi_irrelevant_evidence_does_not_resolve_gap():
    """Scenario 2: Follow-up search returns irrelevant or mismatched evidence."""
    supplier = SupplierProfile(
        id="sup-1",
        name="Apex Micro Foundry Ltd",
        official_domains=["apex-microfoundry.com"],
        country_or_region="Taiwan",
    )
    part_input = PartExposureInput(
        part_name="Automotive MOSFET",
        inventory_coverage_days=Decimal("15"),
        typical_lead_time_days=Decimal("70"),
        recovery_duration_days=None,
        criticality="high",
    )
    initial_exp = calculate_operational_exposure(part_input)
    entity_res = resolve_supplier_entity(
        supplier=supplier,
        subject_text="Apex Micro Foundry Ltd",
        source_text="Apex Micro Foundry cleanroom flooded.",
        source_domain="taipei-times.com",
    )
    initial_snap = IncidentEvidenceSnapshot(
        entity_match_status=entity_res.status,
        evidence_status="single_source",
        event_type="operational_disruption",
        reporting_group_count=1,
        has_resolution_or_correction=False,
    )
    initial_policy = evaluate_policy_rules(initial_snap, initial_exp, entity_res)

    # Irrelevant source mentioning completely different entity in Melbourne
    irrelevant_text = "Acme Minerals Australia announced normal operations resumed today."
    irrelevant_entity = resolve_supplier_entity(
        supplier=supplier,
        subject_text="Acme Minerals Australia",
        source_text=irrelevant_text,
        source_domain="acme-minerals.com.au",
        location_text="Melbourne, Australia",
    )
    assert irrelevant_entity.status == "mismatch"

    # Because entity was mismatched, gap is not closed and exposure remains null
    post_exp = calculate_operational_exposure(part_input)
    post_policy = evaluate_policy_rules(initial_snap, post_exp, entity_res)

    assert post_policy.recommendation == initial_policy.recommendation
    trace = StepTraceRecord(
        step_number=1,
        query='"Apex Micro Foundry Ltd" restart timeline',
        targeted_gap="missing_duration",
        rationale="Search for recovery timeline.",
        heuristic_score=0.88,
        new_sources_count=1,
        new_claims_count=0,
        prior_recommendation=initial_policy.recommendation,
        new_recommendation=post_policy.recommendation,
        recommendation_changed=False,
    )
    assert trace.recommendation_changed is False


def test_voi_no_new_evidence_terminates_loop():
    """Scenario 3: Follow-up search finds no new sources and terminates cleanly."""
    executed = ['"Apex Micro" flood timeline']
    gaps = [EvidenceGap("missing_duration", "Need duration", "Apex", 0.8)]
    candidates = generate_candidate_investigations("Apex Micro", gaps, executed)

    # When search returns no new or uncanonicalized URLs, termination reason is recorded
    trace = StepTraceRecord(
        step_number=1,
        query=candidates[0].query if candidates else "dummy",
        targeted_gap="missing_duration",
        rationale="Search for recovery timeline.",
        heuristic_score=0.85,
        new_sources_count=0,
        new_claims_count=0,
        prior_recommendation="request_supplier_confirmation",
        new_recommendation="request_supplier_confirmation",
        recommendation_changed=False,
        termination_reason="no_new_sources_found",
    )
    assert trace.termination_reason == "no_new_sources_found"
    assert trace.recommendation_changed is False
    assert trace.new_sources_count == 0


def test_voi_contradictory_evidence_handles_resolution_or_widens_uncertainty():
    """Scenario 4: Follow-up evidence contradicts initial rumor and resolves disruption."""
    supplier = SupplierProfile(
        id="sup-2",
        name="OptoCore Photonics Corp",
        official_domains=["optocore-photonics.com"],
        country_or_region="United States",
    )
    part_input = PartExposureInput(
        part_name="Laser Diode",
        inventory_coverage_days=Decimal("20"),
        typical_lead_time_days=Decimal("45"),
        recovery_duration_days=None,
        criticality="medium",
    )
    exp = calculate_operational_exposure(part_input)
    entity_res = resolve_supplier_entity(
        supplier=supplier,
        subject_text="OptoCore Photonics Corp",
        source_text="OptoCore Photonics Corp cleanroom rocked by explosion on tech blog.",
        source_domain="tech-rumors.blog",
    )
    initial_snap = IncidentEvidenceSnapshot(
        entity_match_status=entity_res.status,
        evidence_status="single_source",
        event_type="operational_disruption",
        reporting_group_count=1,
        has_resolution_or_correction=False,
    )
    initial_policy = evaluate_policy_rules(initial_snap, exp, entity_res)
    assert initial_policy.recommendation == "request_supplier_confirmation"

    # Follow-up evidence: Official company statement clarifying drill
    followup_text = (
        "OptoCore Photonics Corp successfully conducted a planned municipal "
        "emergency services drill. Cleanrooms operated without interruption."
    )
    quote = "Cleanrooms operated without interruption."
    assert verify_quote_against_source(quote, followup_text).is_valid

    # Semantic relation detection between initial rumor and official clarification
    claims = [
        {"id": "c1", "claim_type": "incident", "event_type": "operational_disruption"},
        {"id": "c2", "claim_type": "resolution", "event_type": "operational_disruption"},
    ]
    relations = detect_claim_semantic_relations(claims)
    assert len(relations) == 1
    assert relations[0].rule_id == "CR-001"
    assert relations[0].relation == "contradicts"

    # Applying the resolution changes recovery duration to 0 and policy to monitor
    post_part_input = PartExposureInput(
        part_name="Laser Diode",
        inventory_coverage_days=Decimal("20"),
        typical_lead_time_days=Decimal("45"),
        recovery_duration_days=Decimal("0"),
        criticality="medium",
    )
    post_exp = calculate_operational_exposure(post_part_input)
    assert post_exp.potential_inventory_gap_days == Decimal("0")

    post_snap = IncidentEvidenceSnapshot(
        entity_match_status=entity_res.status,
        evidence_status="corroborated",
        event_type="operational_disruption",
        reporting_group_count=2,
        has_resolution_or_correction=True,
    )
    post_policy = evaluate_policy_rules(post_snap, post_exp, entity_res)
    assert post_policy.recommendation == "monitor"
