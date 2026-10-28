"""Evaluation Benchmark Runner for SupplyChain Sentinel.

Performs a rigorous 3-way comparative evaluation across 20 versioned benchmark cases:
1. Baseline LLM Approach: Raw prompt + ungrounded summary/recommendation without deterministic verification.
2. SupplyChain Sentinel (1-Shot Deterministic): Lineage clustering, Rule E-005 exact quote validation,
   ID rules, null-safe range exposure math, and deterministic policy rules.
3. SupplyChain Sentinel + Bounded Next-Best-Investigation (VOI): Proactively closes evidentiary gaps,
   disambiguates unverified reports, bounds missing durations, and tracks decision changes.

Outputs:
- Per-case detailed findings.
- 3-way comparative metrics with explicit mathematical denominators and eligibility criteria.
- Persisted JSON report at evaluation/evaluation_results.json.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

# Ensure backend is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.pipeline.claim_validator import verify_quote_against_source
from app.pipeline.entity_resolution import SupplierProfile, resolve_supplier_entity
from app.pipeline.evidence_graph import detect_claim_semantic_relations
from app.pipeline.exposure_calculator import (
    PartExposureInput,
    calculate_operational_exposure,
)
from app.pipeline.policy_engine import (
    IncidentEvidenceSnapshot,
    evaluate_policy_rules,
)
from app.pipeline.source_lineage import SourceCandidate, analyze_source_lineage
from app.pipeline.source_normalizer import canonicalize_url, compute_content_hash


@dataclass
class CaseEvaluationResult:
    case_id: str
    case_name: str
    expected_policy: str
    expected_escalation: bool
    evaluation_flags: dict[str, bool] = field(default_factory=dict)

    # Sentinel 1-Shot results
    sentinel_attribution: str = ""
    sentinel_attribution_correct: bool = False
    sentinel_quotes_verified: bool = False
    sentinel_duplicates_handled: bool = False
    sentinel_exposure_gap: float | None = None
    sentinel_policy: str = ""
    sentinel_escalated: bool = False
    sentinel_handled_uncertainty: bool = False

    # Sentinel + Next-Best-Investigation (VOI) results
    voi_enabled: bool = False
    voi_executed: bool = False
    voi_policy: str = ""
    voi_decision_changed: bool = False
    voi_accuracy_match: bool = False

    # Baseline results (recorded ungrounded LLM)
    baseline_attribution: str = ""
    baseline_attribution_correct: bool = False
    baseline_quotes_verified: bool = False
    baseline_duplicates_handled: bool = False
    baseline_policy: str = ""
    baseline_escalated: bool = False
    baseline_handled_uncertainty: bool = False


def format_metric_value(num: int, denom: int) -> float | str:
    """Format rate as percentage rounded to 1 decimal place, or 'unavailable' if denominator is 0."""
    if denom == 0:
        return "unavailable"
    return round((num / denom) * 100.0, 1)


def make_metric_entry(
    description: str,
    numerator_def: str,
    denominator_def: str,
    eligible_cases: list[CaseEvaluationResult],
    s1_num: int,
    svoi_num: int,
    base_num: int,
) -> dict[str, Any]:
    denom = len(eligible_cases)
    return {
        "description": description,
        "numerator_definition": numerator_def,
        "denominator_definition": denominator_def,
        "eligible_cases_count": denom,
        "eligible_case_ids": [r.case_id for r in eligible_cases],
        "sentinel_1shot": format_metric_value(s1_num, denom),
        "sentinel_voi": format_metric_value(svoi_num, denom),
        "baseline": format_metric_value(base_num, denom),
    }


def run_evaluation(
    dataset_path: Path | None = None,
    dataset_override: dict[str, Any] | None = None,
    save_output: bool = True,
) -> dict[str, Any]:
    if dataset_override is not None:
        dataset = dataset_override
    else:
        path = dataset_path or (Path(__file__).parent / "benchmark_dataset_v1.json")
        with path.open(encoding="utf-8") as f:
            dataset = json.load(f)

    results: list[CaseEvaluationResult] = []

    for case in dataset["cases"]:
        c_id = case["id"]
        c_name = case["name"]
        target = case["target_supplier"]
        sources = case["sources"]
        claim = case["extracted_claim"]
        base_eval = case["baseline_evaluation"]
        expected_policy = case["expected_policy_recommendation"]
        expected_escalate = case["should_escalate"]
        eval_flags = case.get("evaluation_flags", {})
        tests_wire_dedup = eval_flags.get("tests_wire_deduplication", False)
        tests_uncertainty = eval_flags.get("tests_uncertainty_handling", False)

        # ---- 1. RUN SUPPLYCHAIN SENTINEL (1-SHOT) ----
        # A. Normalization & Lineage Clustering
        source_records: list[SourceCandidate] = []
        for i, s in enumerate(sources):
            canon_url = canonicalize_url(s["url"])
            c_hash = compute_content_hash(s["text"])
            source_records.append(
                SourceCandidate(
                    id=f"src-{i + 1}",
                    url_original=s["url"],
                    url_canonical=canon_url,
                    title=s["publisher"],
                    domain=s["domain"],
                    content_text=s["text"],
                    content_hash=c_hash,
                )
            )

        lineage_res = analyze_source_lineage(source_records)

        # B. Claim Extraction & Rule E-005 Exact Quote Verification
        quote_text = claim.get("supporting_quote", "")
        quotes_valid = any(
            verify_quote_against_source(quote_text, s["text"]).is_valid for s in sources
        )

        # C. Multi-Signal Entity Resolution (ID-001 to ID-005)
        sup_target = SupplierProfile(
            id=f"sup-{c_id}",
            name=target["name"],
            aliases=target.get("aliases", []),
            official_domains=target.get("official_domains", []),
            country_or_region=target.get("country"),
        )

        entity_res = resolve_supplier_entity(
            supplier=sup_target,
            subject_text=claim["subject_entity_name"],
            source_text=sources[0]["text"],
            source_domain=sources[0]["domain"],
            location_text=claim.get("location"),
        )

        # Attribution check: matches expected status, or defensive non-confirmation
        sentinel_attr_correct = entity_res.status == case[
            "expected_identity_status"
        ] or (
            case["expected_identity_status"] in ("mismatch", "ambiguous")
            and entity_res.status in ("mismatch", "ambiguous")
        )

        # D. Operational Exposure Calculation (EX-001 to EX-006)
        part_info = target["parts"][0]
        cov_days = (
            Decimal(str(part_info["inventory_coverage_days"]))
            if part_info.get("inventory_coverage_days") is not None
            else None
        )
        lead_days = (
            Decimal(str(part_info["typical_lead_time_days"]))
            if part_info.get("typical_lead_time_days") is not None
            else None
        )
        duration_val = claim.get("estimated_duration_days")
        extracted_duration = (
            Decimal(str(duration_val))
            if duration_val is not None and duration_val > 0
            else (Decimal(0) if duration_val == 0 else None)
        )

        part_input = PartExposureInput(
            part_name=part_info["part_name"],
            inventory_coverage_days=cov_days,
            typical_lead_time_days=lead_days,
            recovery_duration_days=extracted_duration,
            alternative_available=part_info.get("alternative_available", "no"),
            criticality=part_info["criticality"],
        )

        exposure_res = calculate_operational_exposure(part_input)
        gap_days = (
            float(exposure_res.potential_inventory_gap_days)
            if exposure_res.potential_inventory_gap_days is not None
            else None
        )

        # E. Policy Rulebook Evaluation (P-001 to P-010)
        evidence_snap = IncidentEvidenceSnapshot(
            entity_match_status=entity_res.status,
            evidence_status="corroborated"
            if lineage_res.independent_support_count > 1
            else "single_source",
            event_type=claim.get("event_type"),
            reporting_group_count=lineage_res.reporting_group_count,
            has_resolution_or_correction=claim.get("has_resolution", False),
        )

        policy_res = evaluate_policy_rules(evidence_snap, exposure_res, entity_res)
        sentinel_rec = policy_res.recommendation
        sentinel_escalated = sentinel_rec in (
            "urgent_human_review",
            "review_contingency_plan",
        )

        # Uncertainty handling check: dynamically evaluated for cases testing uncertainty
        sentinel_handled_uncertainty = True
        if tests_uncertainty and (
            case["expected_disruption_days"] is None
            and (gap_days is not None or sentinel_rec == "urgent_human_review")
        ):
            sentinel_handled_uncertainty = False

        # Duplicate wire handling check: dynamically evaluated for cases testing wire deduplication
        sentinel_dup_handled = True
        if tests_wire_dedup and (
            lineage_res.independent_support_count > case["expected_independent_sources"]
        ):
            sentinel_dup_handled = False

        # ---- 2. RUN SENTINEL + BOUNDED NEXT-BEST-INVESTIGATION (VOI) ----
        voi_data = case.get("voi_followup")
        if voi_data:
            voi_source = voi_data["source"]
            post_sources = sources + [voi_source]
            post_source_records = [
                SourceCandidate(
                    id=f"src-{idx + 1}",
                    url_original=s["url"],
                    url_canonical=canonicalize_url(s["url"]),
                    title=s["publisher"],
                    domain=s["domain"],
                    content_text=s["text"],
                    content_hash=compute_content_hash(s["text"]),
                )
                for idx, s in enumerate(post_sources)
            ]
            post_lineage = analyze_source_lineage(post_source_records)

            followup_claim = voi_data.get("extracted_claim")
            followup_valid = False
            followup_has_resolution = False
            followup_duration: Decimal | None = None

            if followup_claim:
                # 1. Exact quote verification on follow-up evidence (Rule E-005)
                f_quote = followup_claim.get("supporting_quote")
                f_quote_valid = verify_quote_against_source(
                    f_quote, voi_source.get("text", "")
                ).is_valid

                # 2. Multi-signal entity resolution on follow-up evidence
                f_entity = resolve_supplier_entity(
                    supplier=sup_target,
                    subject_text=followup_claim.get("subject_entity_name", ""),
                    source_text=voi_source.get("text", ""),
                    source_domain=voi_source.get("domain", ""),
                    location_text=followup_claim.get("location"),
                )

                if f_quote_valid and f_entity.status in ("confirmed", "probable"):
                    followup_valid = True

                    # 3. Detect claim-level semantic relations (Rule CR-001 Contradiction / Resolution)
                    initial_claim_dict = {
                        "id": f"{c_id}-claim-1",
                        "claim_type": claim.get("claim_type", "incident"),
                        "event_type": claim.get("event_type", "operational_disruption"),
                        "source_id": "src-1",
                    }
                    followup_claim_dict = {
                        "id": f"{c_id}-claim-voi",
                        "claim_type": followup_claim.get("claim_type", "incident"),
                        "event_type": followup_claim.get(
                            "event_type", "operational_disruption"
                        ),
                        "source_id": f"src-{len(post_sources)}",
                    }
                    semantic_relations = detect_claim_semantic_relations(
                        [initial_claim_dict, followup_claim_dict]
                    )

                    is_contradiction = any(
                        r.rule_id == "CR-001" and r.relation == "contradicts"
                        for r in semantic_relations
                    )

                    if is_contradiction or followup_claim.get("has_resolution", False):
                        followup_has_resolution = True
                        followup_duration = Decimal(0)
                    elif followup_claim.get("estimated_duration_days") is not None:
                        followup_duration = Decimal(
                            str(followup_claim["estimated_duration_days"])
                        )

            if followup_valid:
                post_duration = (
                    followup_duration
                    if followup_duration is not None
                    else extracted_duration
                )
                post_has_resolution = followup_has_resolution or claim.get(
                    "has_resolution", False
                )
            else:
                post_duration = extracted_duration
                post_has_resolution = claim.get("has_resolution", False)

            post_part_input = PartExposureInput(
                part_name=part_info["part_name"],
                inventory_coverage_days=cov_days,
                typical_lead_time_days=lead_days,
                recovery_duration_days=post_duration,
                alternative_available=part_info.get("alternative_available", "no"),
                criticality=part_info["criticality"],
            )
            post_exposure = calculate_operational_exposure(post_part_input)

            post_snap = IncidentEvidenceSnapshot(
                entity_match_status=entity_res.status,
                evidence_status="corroborated"
                if post_lineage.independent_support_count > 1
                else "single_source",
                event_type=claim.get("event_type"),
                reporting_group_count=post_lineage.reporting_group_count,
                has_resolution_or_correction=post_has_resolution,
            )
            post_policy = evaluate_policy_rules(post_snap, post_exposure, entity_res)

            voi_policy = post_policy.recommendation
            voi_decision_changed = voi_policy != sentinel_rec
            voi_accuracy_match = voi_policy == voi_data.get("post_voi_recommendation")
            voi_executed = True
        else:
            voi_policy = sentinel_rec
            voi_decision_changed = False
            voi_accuracy_match = sentinel_rec == expected_policy
            voi_executed = False

        # ---- 3. RECORD BASELINE SIMULATION (Ungrounded LLM) ----
        baseline_rec = base_eval["recommendation"]
        baseline_escalated = base_eval["escalated"]
        baseline_attr_correct = base_eval["attribution_correct"]
        baseline_quotes_valid = base_eval["quotes_valid"]
        baseline_dup_handled = base_eval["duplicates_handled"]
        baseline_uncertainty = base_eval["handled_uncertainty"]

        results.append(
            CaseEvaluationResult(
                case_id=c_id,
                case_name=c_name,
                expected_policy=expected_policy,
                expected_escalation=expected_escalate,
                evaluation_flags=eval_flags,
                sentinel_attribution=entity_res.status,
                sentinel_attribution_correct=sentinel_attr_correct,
                sentinel_quotes_verified=quotes_valid,
                sentinel_duplicates_handled=sentinel_dup_handled,
                sentinel_exposure_gap=gap_days,
                sentinel_policy=sentinel_rec,
                sentinel_escalated=sentinel_escalated,
                sentinel_handled_uncertainty=sentinel_handled_uncertainty,
                voi_enabled=True,
                voi_executed=voi_executed,
                voi_policy=voi_policy,
                voi_decision_changed=voi_decision_changed,
                voi_accuracy_match=voi_accuracy_match,
                baseline_attribution="confirmed",
                baseline_attribution_correct=baseline_attr_correct,
                baseline_quotes_verified=baseline_quotes_valid,
                baseline_duplicates_handled=baseline_dup_handled,
                baseline_policy=baseline_rec,
                baseline_escalated=baseline_escalated,
                baseline_handled_uncertainty=baseline_uncertainty,
            )
        )

    # ---- AGGREGATE METRICS WITH DYNAMIC LABELS AND EXPLICIT FORMULAS ----
    total_cases = len(results)
    non_escalate_cases = [r for r in results if not r.expected_escalation]
    critical_cases = [r for r in results if r.expected_escalation]
    wire_duplicate_cases = [
        r for r in results if r.evaluation_flags.get("tests_wire_deduplication", False)
    ]
    uncertainty_cases = [
        r
        for r in results
        if r.evaluation_flags.get("tests_uncertainty_handling", False)
    ]
    voi_active_cases = [r for r in results if r.voi_executed]

    summary = {
        "dataset_name": dataset.get("name", "Evaluation Benchmark"),
        "dataset_version": dataset.get("version", "1.0"),
        "total_cases": total_cases,
        "evaluation_mode": "deterministic_offline_simulation",
        "simulation_notes": (
            "Offline VOI follow-up evidence executes through live pipeline modules "
            "(claim_validator, entity_resolution, source_lineage, evidence_graph, "
            "exposure_calculator, policy_engine) over versioned deterministic fixture claims. "
            "Production investigation loop uses live search and Nebius Token Factory provider."
        ),
        "systems_compared": [
            "baseline_unstructured_llm",
            "sentinel_1shot_deterministic",
            "sentinel_next_best_investigation_voi",
        ],
        "metrics": {
            "supplier_attribution_accuracy": make_metric_entry(
                description="Correct corporate entity resolution vs naive name matching",
                numerator_def="Cases where resolved entity status matches ground truth or safe non-confirmation",
                denominator_def="Total evaluated benchmark cases",
                eligible_cases=results,
                s1_num=sum(1 for r in results if r.sentinel_attribution_correct),
                svoi_num=sum(1 for r in results if r.sentinel_attribution_correct),
                base_num=sum(1 for r in results if r.baseline_attribution_correct),
            ),
            "supporting_quote_validity": make_metric_entry(
                description="Percentage of extracted quotes verified mathematically as exact substrings",
                numerator_def="Cases where supporting quote matches source document text",
                denominator_def="Total evaluated benchmark cases with extracted quotes",
                eligible_cases=results,
                s1_num=sum(1 for r in results if r.sentinel_quotes_verified),
                svoi_num=sum(1 for r in results if r.sentinel_quotes_verified),
                base_num=sum(1 for r in results if r.baseline_quotes_verified),
            ),
            "duplicate_wire_handling": make_metric_entry(
                description="Accurate clustering of syndicated news wires preventing inflated confidence",
                numerator_def="Cases where independent support count does not exceed expected count",
                denominator_def="Cases explicitly flagged with tests_wire_deduplication=True",
                eligible_cases=wire_duplicate_cases,
                s1_num=sum(
                    1 for r in wire_duplicate_cases if r.sentinel_duplicates_handled
                ),
                svoi_num=sum(
                    1 for r in wire_duplicate_cases if r.sentinel_duplicates_handled
                ),
                base_num=sum(
                    1 for r in wire_duplicate_cases if r.baseline_duplicates_handled
                ),
            ),
            "false_escalation_rate": make_metric_entry(
                description="Percentage of non-critical, irrelevant, or misattributed cases wrongly escalated",
                numerator_def="Cases where policy escalates despite should_escalate=False",
                denominator_def="Cases with should_escalate=False",
                eligible_cases=non_escalate_cases,
                s1_num=sum(1 for r in non_escalate_cases if r.sentinel_escalated),
                svoi_num=sum(1 for r in non_escalate_cases if r.sentinel_escalated),
                base_num=sum(1 for r in non_escalate_cases if r.baseline_escalated),
            ),
            "critical_incident_recall": make_metric_entry(
                description="Recall of genuine critical disruptions requiring procurement intervention",
                numerator_def="Cases where policy escalates when should_escalate=True",
                denominator_def="Cases with should_escalate=True",
                eligible_cases=critical_cases,
                s1_num=sum(1 for r in critical_cases if r.sentinel_escalated),
                svoi_num=sum(
                    1
                    for r in critical_cases
                    if (
                        r.voi_policy
                        in ("urgent_human_review", "review_contingency_plan")
                        if r.voi_executed
                        else r.sentinel_escalated
                    )
                ),
                base_num=sum(1 for r in critical_cases if r.baseline_escalated),
            ),
            "uncertainty_handling_precision": make_metric_entry(
                description="Correct preservation of nulls and blocking strong action when inputs are missing",
                numerator_def="Cases where missing inputs maintain null exposure gap and block false escalation",
                denominator_def="Cases explicitly flagged with tests_uncertainty_handling=True",
                eligible_cases=uncertainty_cases,
                s1_num=sum(
                    1 for r in uncertainty_cases if r.sentinel_handled_uncertainty
                ),
                svoi_num=sum(
                    1 for r in uncertainty_cases if r.sentinel_handled_uncertainty
                ),
                base_num=sum(
                    1 for r in uncertainty_cases if r.baseline_handled_uncertainty
                ),
            ),
            "next_best_investigation_voi_efficiency": {
                "description": "Information gain and decision changes achieved by targeted gap-closing queries",
                "numerator_definition": "Cases where VOI follow-up changed policy recommendation",
                "denominator_definition": "Cases with active VOI follow-up execution",
                "eligible_cases_count": len(voi_active_cases),
                "eligible_case_ids": [r.case_id for r in voi_active_cases],
                "sentinel_1shot": 0.0,
                "sentinel_voi": format_metric_value(
                    sum(1 for r in voi_active_cases if r.voi_decision_changed),
                    len(voi_active_cases),
                ),
                "baseline": 0.0,
                "directional_accuracy_on_change": format_metric_value(
                    sum(1 for r in voi_active_cases if r.voi_accuracy_match),
                    len(voi_active_cases),
                ),
            },
        },
        "case_details": [asdict(r) for r in results],
    }

    if save_output:
        output_path = Path(__file__).parent / "evaluation_results.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    report = run_evaluation()
    print("=" * 82)
    print("SUPPLYCHAIN SENTINEL - 3-WAY COMPARATIVE EVALUATION BENCHMARK")
    print("=" * 82)
    print(f"Total Cases: {report['total_cases']}")
    print("-" * 82)
    print(
        f"{'Metric':<38} | {'Eligible':<8} | {'Baseline':<9} | {'1-Shot':<9} | {'VOI Loop':<9}"
    )
    print("-" * 82)
    for k, v in report["metrics"].items():
        name = k.replace("_", " ").title()[:36]
        cnt = str(v.get("eligible_cases_count", 0))
        b_val = v.get("baseline")
        s1_val = v.get("sentinel_1shot")
        svoi_val = v.get("sentinel_voi")
        base = f"{b_val}%" if isinstance(b_val, (int, float)) else str(b_val)
        s1 = f"{s1_val}%" if isinstance(s1_val, (int, float)) else str(s1_val)
        svoi = f"{svoi_val}%" if isinstance(svoi_val, (int, float)) else str(svoi_val)
        print(f"{name:<38} | {cnt:<8} | {base:<9} | {s1:<9} | {svoi:<9}")
    print("=" * 82)
    print(
        f"Detailed results saved to: {Path(__file__).parent / 'evaluation_results.json'}"
    )
