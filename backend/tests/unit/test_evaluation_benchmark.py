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
    """Verify benchmark_dataset_v1.json exists, contains 20 cases, and adheres to schema."""
    dataset_path = REPO_ROOT / "evaluation" / "benchmark_dataset_v1.json"
    assert dataset_path.exists(), f"Benchmark dataset missing at {dataset_path}"

    with dataset_path.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("version") in ("1.0", "1.0.0")
    cases = data.get("cases", [])
    assert len(cases) == 20, f"Expected 20 benchmark cases, found {len(cases)}"

    case_ids = {c["id"] for c in cases}
    expected_ids = {f"CASE-{i:02d}" for i in range(1, 21)}
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
    """Run evaluation and assert Sentinel's 3-way deterministic and VOI guarantees over baseline."""
    results = run_evaluation()

    assert results["total_cases"] == 20
    assert results["evaluation_mode"] == "3_way_comparison"
    metrics = results["metrics"]

    # Explicit denominators
    assert "20" in metrics["supplier_attribution_accuracy"]["denominator"]
    assert "20" in metrics["supporting_quote_validity"]["denominator"]
    assert "2" in metrics["duplicate_wire_handling"]["denominator"]
    assert "17" in metrics["false_escalation_rate"]["denominator"]
    assert "3" in metrics["critical_incident_recall"]["denominator"]
    assert "2" in metrics["uncertainty_handling_precision"]["denominator"]

    # Sentinel deterministic metrics (in percentage points 0-100)
    assert metrics["supplier_attribution_accuracy"]["sentinel_1shot"] >= 90.0
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
