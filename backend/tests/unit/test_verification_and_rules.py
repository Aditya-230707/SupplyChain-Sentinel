"""
Unit tests for verification algorithms and deterministic policy rules.

Covers:
- URL canonicalization and duplicate grouping (E-001, E-002, E-008)
- Source lineage and syndication (E-003, EV-001, EV-002)
- Exact quote verification against stored text (E-005)
- Multi-signal entity resolution (ID-001 to ID-005)
- Deterministic operational exposure calculation (EX-001 to EX-006)
- Deterministic policy rules (P-001 to P-010)
"""

from __future__ import annotations

from decimal import Decimal

from app.pipeline.claim_validator import verify_quote_against_source
from app.pipeline.entity_resolution import (
    SupplierProfile,
    resolve_supplier_entity,
)
from app.pipeline.exposure_calculator import (
    PartExposureInput,
    calculate_operational_exposure,
)
from app.pipeline.policy_engine import (
    IncidentEvidenceSnapshot,
    evaluate_policy_rules,
)
from app.pipeline.source_lineage import (
    SourceCandidate,
    analyze_source_lineage,
)
from app.pipeline.source_normalizer import (
    canonicalize_url,
    title_similarity_jaccard,
)

# ---- 1. URL Normalization (E-001, E-008) ---------------------


def test_url_canonicalization_strips_tracking_params() -> None:
    raw_url = "https://www.example.com/news/article?id=123&utm_source=twitter&utm_medium=social&fbclid=XYZ#comments"
    canonical = canonicalize_url(raw_url)
    assert canonical == "https://www.example.com/news/article?id=123"


def test_url_canonicalization_normalizes_case_and_ports() -> None:
    raw_url = "HTTP://EXAMPLE.COM:80/path/to/page/"
    canonical = canonicalize_url(raw_url)
    assert canonical == "http://example.com/path/to/page"


def test_title_similarity_detects_near_duplicates() -> None:
    t1 = "Fire breaks out at Acme Corp factory in Dresden"
    t2 = "Fire reported at Acme Corp factory in Dresden"
    sim = title_similarity_jaccard(t1, t2)
    assert sim >= 0.5  # shared tokens: fire, acme, corp, factory, dresden


# ---- 2. Source Lineage & Non-Independent Sources (E-003, EV-001, EV-002) -


def test_lineage_groups_syndicated_reuters_reports() -> None:
    s1 = SourceCandidate(
        id="s1",
        url_original="https://news-site-a.com/article-1",
        url_canonical="https://news-site-a.com/article-1",
        title="Supplier plant shut down",
        publisher_name="Site A",
        content_text="Reuters reports that the plant was halted today.",
    )
    s2 = SourceCandidate(
        id="s2",
        url_original="https://news-site-b.com/reprint",
        url_canonical="https://news-site-b.com/reprint",
        title="Supplier plant shut down",
        publisher_name="Site B",
        content_text="According to Reuters, operations ceased this morning.",
    )

    lineage = analyze_source_lineage([s1, s2])
    assert lineage.source_count == 2
    # Even though there are 2 URLs, they share Reuters origin -> 1 reporting group
    assert lineage.reporting_group_count == 1
    assert lineage.independent_support_count == 1


def test_lineage_detects_independent_sources() -> None:
    s1 = SourceCandidate(
        id="s1",
        url_original="https://regulator.gov/enforcement/notice-44",
        url_canonical="https://regulator.gov/enforcement/notice-44",
        title="Official Environmental Sanction",
        publisher_name="Environmental Protection Agency",
        content_text="The agency has issued an order regarding wastewater violations.",
    )
    s2 = SourceCandidate(
        id="s2",
        url_original="https://local-investigative-times.com/special-report",
        url_canonical="https://local-investigative-times.com/special-report",
        title="Investigative Report: Factory Effluent Concerns",
        publisher_name="Independent Investigative Daily",
        content_text="Our independent testing found elevated chemical runoff near the perimeter.",
    )

    lineage = analyze_source_lineage([s1, s2])
    assert lineage.source_count == 2
    assert lineage.reporting_group_count == 2
    assert lineage.independent_support_count == 2


# ---- 3. Quote Verification (E-005) ----------------------------


def test_quote_verification_exact_match() -> None:
    source_text = "On Monday, a major blaze destroyed warehouse 3 at the manufacturing campus."
    quote = "a major blaze destroyed warehouse 3"
    result = verify_quote_against_source(quote, source_text)
    assert result.is_valid is True
    assert result.status == "validated"
    assert result.quote_start is not None


def test_quote_verification_whitespace_variation() -> None:
    source_text = "Production was halted\n    indefinitely following\tstructural damage."
    quote = "Production was halted indefinitely following structural damage."
    result = verify_quote_against_source(quote, source_text)
    assert result.is_valid is True
    assert result.status == "validated"


def test_quote_verification_fabricated_quote_fails() -> None:
    source_text = "The facility had a small electrical spark which was extinguished in 5 minutes."
    fabricated_quote = "The facility suffered catastrophic total destruction."
    result = verify_quote_against_source(fabricated_quote, source_text)
    assert result.is_valid is False
    assert result.status == "quote_mismatch"
    assert "not found" in (result.mismatch_reason or "")


# ---- 4. Multi-Signal Entity Resolution (ID-001 to ID-005) -----


def test_entity_resolution_confirmed_via_domain() -> None:
    supplier = SupplierProfile(
        id="sup-1",
        name="Apex Photonics Inc",
        official_domains=["apexphotonics.com"],
        country_or_region="Germany",
    )
    res = resolve_supplier_entity(
        supplier=supplier,
        subject_text="Apex Photonics Inc",
        source_domain="press.apexphotonics.com",
    )
    assert res.status == "confirmed"
    assert "official_domain" in res.matched_signals


def test_entity_resolution_common_name_without_secondary_signal_is_ambiguous() -> None:
    """Rule ID-001: Short common name alone cannot be confirmed."""
    supplier = SupplierProfile(
        id="sup-2",
        name="Apex Corp",
        country_or_region="Germany",
    )
    res = resolve_supplier_entity(
        supplier=supplier,
        subject_text="Apex Corp",
        source_text="Apex Corp announced a closure of its facilities.",
        location_text="Singapore",  # Location mismatch/unrelated
    )
    assert res.status == "ambiguous"
    assert any("short/common name" in r for r in res.ambiguity_reasons)


def test_entity_resolution_different_entity_is_mismatch() -> None:
    supplier = SupplierProfile(id="sup-3", name="Continental Bearings Ltd")
    res = resolve_supplier_entity(
        supplier=supplier,
        subject_text="Zenith Semiconductors LLC",
        source_text="Zenith Semiconductors LLC reported a warehouse fire.",
    )
    assert res.status == "mismatch"


# ---- 5. Deterministic Operational Exposure (EX-001 to EX-006) -


def test_exposure_known_positive_gap() -> None:
    """Rule EX-003: gap = max(0, duration - coverage)."""
    part = PartExposureInput(
        part_name="Microcontroller IC",
        inventory_coverage_days=Decimal("20"),
        typical_lead_time_days=Decimal("45"),
        recovery_duration_days=Decimal("35"),
        recovery_provenance="source_evidence",
        criticality="high",
    )
    res = calculate_operational_exposure(part)
    # 35 - 20 = 15 days gap
    assert res.potential_inventory_gap_days == Decimal("15")
    assert res.exposure_band == "high"


def test_exposure_sufficient_inventory_zero_gap() -> None:
    part = PartExposureInput(
        part_name="Standard Resistor",
        inventory_coverage_days=Decimal("60"),
        typical_lead_time_days=Decimal("15"),
        recovery_duration_days=Decimal("30"),
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days == Decimal("0")
    assert res.exposure_band == "low"


def test_exposure_missing_duration_leaves_gap_null() -> None:
    """Rule EX-002: Unknown duration leaves gap as None, never 0."""
    part = PartExposureInput(
        part_name="Custom Sensor",
        inventory_coverage_days=Decimal("30"),
        typical_lead_time_days=Decimal("40"),
        recovery_duration_days=None,  # unknown
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days is None
    assert res.exposure_band == "unknown"
    assert any("Disruption duration is unknown" in lim for lim in res.limitations)


# ---- 6. Deterministic Policy Engine (P-001 to P-010) ----------


def test_policy_blocks_strong_action_on_ambiguous_identity() -> None:
    """Rule P-001: Ambiguous identity yields request_supplier_confirmation, blocks urgent action."""
    snapshot = IncidentEvidenceSnapshot(
        entity_match_status="ambiguous",
        evidence_status="corroborated",
        event_type="operational_disruption",
        reporting_group_count=3,
    )
    from app.pipeline.entity_resolution import EntityResolutionResult
    from app.pipeline.exposure_calculator import ExposureResult

    entity = EntityResolutionResult(
        status="ambiguous",
        ambiguity_reasons=["Common company name; secondary signal missing"],
    )
    exposure = ExposureResult(
        potential_inventory_gap_days=Decimal("30"),
        exposure_band="high",
        criticality="high",
        alternative_available="no",
        calculation_name="inventory_gap_v1",
        calculation_version="1.0",
        input_values={},
    )

    decision = evaluate_policy_rules(snapshot, exposure, entity)
    assert decision.recommendation == "request_supplier_confirmation"
    assert "P-001" in decision.rule_ids_fired
    assert decision.human_review_required is True
    assert any("Ambiguous supplier identity" in r for r in decision.reasons)


def test_policy_disputed_evidence_requires_human_review() -> None:
    """Rule P-003: Disputed evidence requires human review."""
    snapshot = IncidentEvidenceSnapshot(
        entity_match_status="confirmed",
        evidence_status="disputed",
        event_type="operational_disruption",
        reporting_group_count=2,
        has_contradictions=True,
    )
    from app.pipeline.entity_resolution import EntityResolutionResult
    from app.pipeline.exposure_calculator import ExposureResult

    entity = EntityResolutionResult(status="confirmed")
    exposure = ExposureResult(
        potential_inventory_gap_days=Decimal("10"),
        exposure_band="moderate",
        criticality="medium",
        alternative_available="yes",
        calculation_name="inventory_gap_v1",
        calculation_version="1.0",
        input_values={},
    )

    decision = evaluate_policy_rules(snapshot, exposure, entity)
    assert decision.recommendation == "urgent_human_review"
    assert "P-003" in decision.rule_ids_fired
    assert decision.human_review_required is True


def test_policy_positive_gap_recommends_contingency_or_urgent() -> None:
    """Rule P-005: Positive gap recommends review_contingency_plan or urgent_human_review."""
    snapshot = IncidentEvidenceSnapshot(
        entity_match_status="confirmed",
        evidence_status="corroborated",
        event_type="operational_disruption",
        reporting_group_count=2,
    )
    from app.pipeline.entity_resolution import EntityResolutionResult
    from app.pipeline.exposure_calculator import ExposureResult

    entity = EntityResolutionResult(status="confirmed")
    exposure = ExposureResult(
        potential_inventory_gap_days=Decimal("20"),
        exposure_band="high",
        criticality="high",
        alternative_available="no",
        calculation_name="inventory_gap_v1",
        calculation_version="1.0",
        input_values={},
    )

    decision = evaluate_policy_rules(snapshot, exposure, entity)
    assert decision.recommendation == "urgent_human_review"
    assert "P-005" in decision.rule_ids_fired


def test_policy_resolved_event_recommends_monitor_only() -> None:
    """Rule P-007: Resolved event is marked monitor."""
    snapshot = IncidentEvidenceSnapshot(
        entity_match_status="confirmed",
        evidence_status="outdated_or_resolved",
        event_type="operational_disruption",
        reporting_group_count=2,
        has_resolution_or_correction=True,
    )
    from app.pipeline.entity_resolution import EntityResolutionResult
    from app.pipeline.exposure_calculator import ExposureResult

    entity = EntityResolutionResult(status="confirmed")
    exposure = ExposureResult(
        potential_inventory_gap_days=Decimal("0"),
        exposure_band="low",
        criticality="low",
        alternative_available="yes",
        calculation_name="inventory_gap_v1",
        calculation_version="1.0",
        input_values={},
    )

    decision = evaluate_policy_rules(snapshot, exposure, entity)
    assert decision.recommendation == "monitor"
    assert "P-007" in decision.rule_ids_fired
    assert decision.human_review_required is False
