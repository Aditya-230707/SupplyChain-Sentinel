"""
Deterministic policy engine for SupplyChain Sentinel.

Implements Rules P-001 to P-010:
Consumes validated structured records and returns a deterministic recommendation.
Does NOT invoke an LLM to choose or bypass rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.pipeline.entity_resolution import EntityResolutionResult
from app.pipeline.exposure_calculator import ExposureResult


@dataclass
class IncidentEvidenceSnapshot:
    entity_match_status: str  # confirmed | probable | ambiguous | mismatch | unknown
    evidence_status: (
        str  # primary_source_reported | corroborated | single_source | disputed | unverified
    )
    event_type: (
        str | None
    )  # operational_disruption | environmental_regulatory | logistics_disruption | other
    reporting_group_count: int
    has_contradictions: bool = False
    has_resolution_or_correction: bool = False
    provider_failed: bool = False


@dataclass
class PolicyEvaluationResult:
    policy_version: str
    # monitor | request_supplier_confirmation | review_contingency_plan | urgent_human_review
    recommendation: str
    rule_ids_fired: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    human_review_required: bool = True
    input_snapshot: dict[str, Any] = field(default_factory=dict)


def evaluate_policy_rules(
    evidence: IncidentEvidenceSnapshot,
    exposure: ExposureResult,
    entity: EntityResolutionResult,
) -> PolicyEvaluationResult:
    """Evaluate deterministic policy rules in strict priority order.

    Order:
    1. Provider / data failures (P-008)
    2. Identity blockers (P-001, ID-004)
    3. Resolved / outdated events (P-007)
    4. Disputed / contradictory evidence (P-003)
    5. Single-origin / unverified reports (P-002)
    6. Exposure evaluation (P-004, P-005)
    7. Regulatory events (P-006)
    """
    rules_fired: list[str] = []
    reasons: list[str] = []
    blockers: list[str] = []
    recommendation = "monitor"
    review_required = True

    input_snapshot = {
        "entity_match_status": entity.status,
        "evidence_status": evidence.evidence_status,
        "event_type": evidence.event_type,
        "reporting_group_count": evidence.reporting_group_count,
        "inventory_gap_days": float(exposure.potential_inventory_gap_days)
        if exposure.potential_inventory_gap_days is not None
        else None,
        "exposure_band": exposure.exposure_band,
        "criticality": exposure.criticality,
    }

    # 1. P-008: Tool / Provider failure
    if evidence.provider_failed:
        rules_fired.append("P-008")
        blockers.append("Data retrieval or model extraction experienced a provider failure.")
        reasons.append("Cannot reach definitive recommendation due to partial provider failure.")
        return PolicyEvaluationResult(
            policy_version="1.0",
            recommendation="insufficient_evidence",
            rule_ids_fired=rules_fired,
            reasons=reasons,
            blockers=blockers,
            human_review_required=True,
            input_snapshot=input_snapshot,
        )

    # 2. P-001 / ID-004: Identity blockers
    if entity.status in ("ambiguous", "mismatch", "unknown"):
        rules_fired.append("P-001")
        ambig_detail = "; ".join(entity.ambiguity_reasons) or "no identifiers"
        blockers.append(f"Supplier identity match is '{entity.status}' ({ambig_detail}).")
        if entity.status == "mismatch":
            reasons.append(
                "Evidence indicates a different corporate entity than the target supplier."
            )
            return PolicyEvaluationResult(
                policy_version="1.0",
                recommendation="insufficient_evidence",
                rule_ids_fired=rules_fired,
                reasons=reasons,
                blockers=blockers,
                human_review_required=False,
                input_snapshot=input_snapshot,
            )
        reasons.append("Ambiguous supplier identity blocks any high-impact recommendation.")
        return PolicyEvaluationResult(
            policy_version="1.0",
            recommendation="request_supplier_confirmation",
            rule_ids_fired=rules_fired,
            reasons=reasons,
            blockers=blockers,
            human_review_required=True,
            input_snapshot=input_snapshot,
        )

    # 3. P-007: Explicitly resolved or corrected event
    if evidence.has_resolution_or_correction or evidence.evidence_status == "outdated_or_resolved":
        rules_fired.append("P-007")
        reasons.append(
            "Evidence indicates the incident is historically documented but resolved or corrected."
        )
        return PolicyEvaluationResult(
            policy_version="1.0",
            recommendation="monitor",
            rule_ids_fired=rules_fired,
            reasons=reasons,
            blockers=[],
            human_review_required=False,
            input_snapshot=input_snapshot,
        )

    # 4. P-003: Disputed evidence or structured contradiction
    if evidence.has_contradictions or evidence.evidence_status == "disputed":
        rules_fired.append("P-003")
        reasons.append(
            "Conflicting claims exist regarding event occurrence, severity, or operational impact."
        )
        return PolicyEvaluationResult(
            policy_version="1.0",
            recommendation="urgent_human_review",
            rule_ids_fired=rules_fired,
            reasons=reasons,
            blockers=["Evidence is disputed between sources."],
            human_review_required=True,
            input_snapshot=input_snapshot,
        )

    # 5. Exposure evaluation (P-004, P-005)
    gap = exposure.potential_inventory_gap_days
    if gap is None:
        rules_fired.append("P-004")
        reasons.append(
            "Credible disruption reported, but inventory coverage or duration is unknown."
        )
        blockers.append(
            "Cannot quantify operational impact without verified duration or inventory inputs."
        )
        recommendation = "request_supplier_confirmation"
    elif gap > Decimal("14") or (gap > Decimal("0") and exposure.criticality == "high"):
        rules_fired.append("P-005")
        reasons.append(f"Calculated potential inventory gap of {gap} days exceeds safe threshold.")
        recommendation = "urgent_human_review"
    elif gap > Decimal("0"):
        rules_fired.append("P-005")
        reasons.append(
            f"Calculated potential inventory gap of {gap} days. Contingency review recommended."
        )
        recommendation = "review_contingency_plan"
    else:
        # gap == 0
        reasons.append(
            "Current inventory coverage is sufficient for estimated disruption duration."
        )
        recommendation = "monitor"

    # 6. P-002: Single-source or unverified reporting
    if (
        evidence.evidence_status in ("single_source", "unverified")
        or evidence.reporting_group_count <= 1
    ):
        rules_fired.append("P-002")
        reasons.append(
            "Evidence originates from a single reporting group; independence is uncorroborated."
        )
        blockers.append("Uncorroborated single-origin reporting.")
        if recommendation != "urgent_human_review":
            recommendation = "request_supplier_confirmation"

    # 7. P-006: Environmental regulatory action
    if evidence.event_type == "environmental_regulatory":
        rules_fired.append("P-006")
        reasons.append(
            "Public regulatory enforcement action or notice identified concerning supplier."
        )
        if recommendation != "urgent_human_review":
            recommendation = "review_contingency_plan"

    return PolicyEvaluationResult(
        policy_version="1.0",
        recommendation=recommendation,
        rule_ids_fired=rules_fired,
        reasons=reasons,
        blockers=blockers,
        human_review_required=review_required,
        input_snapshot=input_snapshot,
    )
