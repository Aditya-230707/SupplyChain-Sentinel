"""Unit tests verifying the SupplyChain Sentinel Evaluation Benchmark dataset and pipeline."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from evaluation.runner import run_evaluation  # noqa: E402

REPO_ROOT = _repo_root


def test_benchmark_dataset_integrity() -> None:
    """Verify benchmark_dataset_v1.json exists, contains 20 cases, and adheres to schema."""
    dataset_path = REPO_ROOT / "evaluation" / "benchmark_dataset_v1.json"
    assert dataset_path.exists(), f"Benchmark dataset missing at {dataset_path}"

    with dataset_path.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("version") in ("1.0", "1.0.0")
    cases = data.get("cases", [])
    assert len(cases) == 20, f"Expected 20 benchmark cases, found {len(cases)}"

    case_ids = [c["id"] for c in cases]
    assert len(case_ids) == len(set(case_ids)), "Duplicate case IDs detected in benchmark dataset"

    expected_ids = {f"CASE-{i:02d}" for i in range(1, 21)}
    assert set(case_ids) == expected_ids, f"Mismatch in case IDs: {set(case_ids)} != {expected_ids}"

    wire_dedup_count = 0
    uncertainty_count = 0

    for case in cases:
        assert "target_supplier" in case
        assert "sources" in case
        assert "extracted_claim" in case
        assert "baseline_evaluation" in case
        assert "expected_identity_status" in case
        assert "should_escalate" in case
        assert "expected_policy_recommendation" in case
        assert "evaluation_flags" in case

        flags = case["evaluation_flags"]
        assert isinstance(flags.get("tests_wire_deduplication"), bool)
        assert isinstance(flags.get("tests_uncertainty_handling"), bool)

        if flags["tests_wire_deduplication"]:
            wire_dedup_count += 1
        if flags["tests_uncertainty_handling"]:
            uncertainty_count += 1

    assert wire_dedup_count == 2  # CASE-01, CASE-04
    assert uncertainty_count == 3  # CASE-03, CASE-07, CASE-12


def test_benchmark_runner_execution_and_metrics() -> None:
    """Run evaluation and assert Sentinel's 3-way deterministic and VOI guarantees over baseline."""
    results = run_evaluation(save_output=False)

    assert results["total_cases"] == 20
    assert results["evaluation_mode"] == "deterministic_offline_simulation"
    metrics = results["metrics"]

    # Explicit denominators & eligibility counts
    assert metrics["supplier_attribution_accuracy"]["eligible_cases_count"] == 20
    assert metrics["supporting_quote_validity"]["eligible_cases_count"] == 20
    assert metrics["duplicate_wire_handling"]["eligible_cases_count"] == 2
    assert metrics["false_escalation_rate"]["eligible_cases_count"] == 17
    assert metrics["critical_incident_recall"]["eligible_cases_count"] == 3
    assert metrics["uncertainty_handling_precision"]["eligible_cases_count"] == 3
    assert metrics["next_best_investigation_voi_efficiency"]["eligible_cases_count"] == 2

    # Sentinel deterministic metrics (in percentage points 0-100)
    assert metrics["supplier_attribution_accuracy"]["sentinel_1shot"] == 95.0
    assert metrics["supporting_quote_validity"]["sentinel_1shot"] == 100.0
    assert metrics["duplicate_wire_handling"]["sentinel_1shot"] == 100.0
    assert metrics["false_escalation_rate"]["sentinel_1shot"] == 0.0  # 0% false escalation
    assert metrics["critical_incident_recall"]["sentinel_1shot"] == 100.0  # 100% recall
    assert metrics["uncertainty_handling_precision"]["sentinel_1shot"] == 100.0

    # Sentinel + Next-Best-Investigation VOI efficiency
    assert metrics["next_best_investigation_voi_efficiency"]["sentinel_voi"] == 100.0
    assert (
        metrics["next_best_investigation_voi_efficiency"]["directional_accuracy_on_change"] == 100.0
    )

    # Baseline demonstrates high hallucination/false escalation risks
    assert metrics["false_escalation_rate"]["baseline"] > 80.0
    assert metrics["duplicate_wire_handling"]["baseline"] == 0.0


def test_benchmark_dynamic_denominators() -> None:
    """Verify that adding a correctly flagged case changes denominators without modifying runner."""
    dataset_path = REPO_ROOT / "evaluation" / "benchmark_dataset_v1.json"
    with dataset_path.open(encoding="utf-8") as f:
        base_data = json.load(f)

    # Clone dataset and add a dummy case flagged for wire deduplication and uncertainty
    modified_data = copy.deepcopy(base_data)
    dummy_case = copy.deepcopy(modified_data["cases"][0])
    dummy_case["id"] = "CASE-99"
    dummy_case["name"] = "Dynamic Test Case"
    dummy_case["evaluation_flags"] = {
        "tests_wire_deduplication": True,
        "tests_uncertainty_handling": True,
    }
    dummy_case["expected_disruption_days"] = None
    dummy_case["should_escalate"] = False
    dummy_case["expected_policy_recommendation"] = "insufficient_evidence"

    modified_data["cases"].append(dummy_case)

    results = run_evaluation(dataset_override=modified_data, save_output=False)

    # Wire deduplication denominator must have increased from 2 to 3
    assert results["metrics"]["duplicate_wire_handling"]["eligible_cases_count"] == 3
    assert "CASE-99" in results["metrics"]["duplicate_wire_handling"]["eligible_case_ids"]

    # Uncertainty handling denominator must have increased from 3 to 4
    assert results["metrics"]["uncertainty_handling_precision"]["eligible_cases_count"] == 4
    assert "CASE-99" in results["metrics"]["uncertainty_handling_precision"]["eligible_case_ids"]


def test_benchmark_zero_eligible_cases_reports_unavailable() -> None:
    """Verify that when a metric has 0 eligible cases, it reports 'unavailable' rather than 0.0."""
    dataset_path = REPO_ROOT / "evaluation" / "benchmark_dataset_v1.json"
    with dataset_path.open(encoding="utf-8") as f:
        base_data = json.load(f)

    # Turn off wire deduplication flags across all cases
    modified_data = copy.deepcopy(base_data)
    for c in modified_data["cases"]:
        c["evaluation_flags"]["tests_wire_deduplication"] = False

    results = run_evaluation(dataset_override=modified_data, save_output=False)
    dup_metric = results["metrics"]["duplicate_wire_handling"]

    assert dup_metric["eligible_cases_count"] == 0
    assert dup_metric["sentinel_1shot"] == "unavailable"
    assert dup_metric["sentinel_voi"] == "unavailable"
    assert dup_metric["baseline"] == "unavailable"
