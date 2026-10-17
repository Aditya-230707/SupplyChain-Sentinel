"""Unit test verifying the SupplyChain Sentinel Evaluation Benchmark dataset and pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from evaluation.runner import run_evaluation  # noqa: E402

REPO_ROOT = _repo_root


def test_benchmark_dataset_integrity() -> None:
    """Verify benchmark_dataset_v1.json exists, contains 9 cases, and adheres to schema."""
    dataset_path = REPO_ROOT / "evaluation" / "benchmark_dataset_v1.json"
    assert dataset_path.exists(), f"Benchmark dataset missing at {dataset_path}"

    with dataset_path.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("version") in ("1.0", "1.0.0")
    cases = data.get("cases", [])
    assert len(cases) == 9, f"Expected 9 benchmark cases, found {len(cases)}"

    case_ids = {c["id"] for c in cases}
    expected_ids = {f"CASE-0{i}" for i in range(1, 10)}
    assert case_ids == expected_ids, f"Mismatch in case IDs: {case_ids} != {expected_ids}"

    for case in cases:
        assert "target_supplier" in case
        assert "sources" in case
        assert "extracted_claim" in case
        assert "baseline_evaluation" in case
        assert "expected_identity_status" in case
        assert "should_escalate" in case
        assert "expected_policy_recommendation" in case


def test_benchmark_runner_execution_and_metrics() -> None:
    """Run evaluation and assert Sentinel's deterministic guarantees over baseline."""
    results = run_evaluation()

    assert results["total_cases"] == 9
    metrics = results["metrics"]

    # Explicit denominators
    assert "9" in metrics["supplier_attribution_accuracy"]["denominator"]
    assert "9" in metrics["supporting_quote_validity"]["denominator"]
    assert "2" in metrics["duplicate_wire_handling"]["denominator"]
    assert "8" in metrics["false_escalation_rate"]["denominator"]
    assert "1" in metrics["critical_incident_recall"]["denominator"]
    assert "2" in metrics["uncertainty_handling_precision"]["denominator"]

    # Sentinel deterministic metrics (in percentage points 0-100)
    sentinel_metrics = {k: v["sentinel"] for k, v in metrics.items()}
    assert sentinel_metrics["supplier_attribution_accuracy"] == 100.0
    assert sentinel_metrics["supporting_quote_validity"] == 100.0
    assert sentinel_metrics["duplicate_wire_handling"] == 100.0
    assert sentinel_metrics["false_escalation_rate"] == 0.0  # 0% false escalation
    assert sentinel_metrics["critical_incident_recall"] == 100.0  # 100% recall
    assert sentinel_metrics["uncertainty_handling_precision"] == 100.0

    # Baseline demonstrates high hallucination/false escalation risks
    baseline_metrics = {k: v["baseline"] for k, v in metrics.items()}
    assert baseline_metrics["false_escalation_rate"] > 80.0
    assert baseline_metrics["duplicate_wire_handling"] == 0.0
