"""
Unit tests for Mathematical Exposure Engine and Decision Loss Analysis.

Covers:
- Point gap calculation and null-safety (EX-001, EX-002, EX-003)
- Range propagation: [D_min, D_max] -> [gap_min, gap_max] (EX-004)
- Deterministic scenario projections (Short, Baseline, Extended) (EX-005)
- Expected decision loss optimization under downtime cost (EX-006)
- Sensitivity analysis when financial inputs are absent (EX-007)
"""

from __future__ import annotations

from decimal import Decimal

from app.pipeline.exposure_calculator import (
    PartExposureInput,
    calculate_operational_exposure,
)


def test_exposure_point_gap_positive() -> None:
    part = PartExposureInput(
        part_name="Automotive MCU",
        inventory_coverage_days=Decimal("14"),
        typical_lead_time_days=Decimal("60"),
        recovery_duration_days=Decimal("45"),
        criticality="high",
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days == Decimal("31")
    assert res.exposure_band == "high"
    assert res.calculation_name == "inventory_gap_v2"


def test_exposure_point_gap_sufficient_inventory() -> None:
    part = PartExposureInput(
        part_name="Standard Resistor",
        inventory_coverage_days=Decimal("45"),
        typical_lead_time_days=Decimal("30"),
        recovery_duration_days=Decimal("10"),
        criticality="low",
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days == Decimal("0")
    assert res.exposure_band == "low"


def test_exposure_null_safety_when_duration_missing() -> None:
    part = PartExposureInput(
        part_name="Custom ASIC",
        inventory_coverage_days=Decimal("30"),
        typical_lead_time_days=Decimal("90"),
        recovery_duration_days=None,
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days is None
    assert res.exposure_band == "unknown"
    assert any("Disruption duration is unknown" in limit for limit in res.limitations)


def test_exposure_null_safety_when_inventory_missing() -> None:
    part = PartExposureInput(
        part_name="Custom ASIC",
        inventory_coverage_days=None,
        typical_lead_time_days=Decimal("90"),
        recovery_duration_days=Decimal("30"),
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days is None
    assert res.exposure_band == "unknown"
    assert any("Inventory coverage days is unknown" in limit for limit in res.limitations)


def test_exposure_range_propagation() -> None:
    part = PartExposureInput(
        part_name="Power Management IC",
        inventory_coverage_days=Decimal("20"),
        typical_lead_time_days=Decimal("45"),
        recovery_duration_days=Decimal("40"),
        recovery_duration_min_days=Decimal("30"),
        recovery_duration_max_days=Decimal("60"),
    )
    res = calculate_operational_exposure(part)
    assert res.potential_inventory_gap_days == Decimal("20")
    assert res.potential_inventory_gap_min_days == Decimal("10")
    assert res.potential_inventory_gap_max_days == Decimal("40")


def test_exposure_scenario_projections() -> None:
    part = PartExposureInput(
        part_name="Battery Management Module",
        inventory_coverage_days=Decimal("10"),
        typical_lead_time_days=Decimal("40"),
        recovery_duration_days=Decimal("30"),
    )
    res = calculate_operational_exposure(part)
    assert len(res.scenarios) == 3
    scenario_names = [s["name"] for s in res.scenarios]
    assert "Short Interruption" in scenario_names
    assert "Baseline Grounded" in scenario_names
    assert "Extended Disruption" in scenario_names

    baseline = next(s for s in res.scenarios if s["name"] == "Baseline Grounded")
    assert baseline["inventory_gap_days"] == 20.0


def test_exposure_expected_decision_loss_computed_when_cost_provided() -> None:
    part = PartExposureInput(
        part_name="Critical Sensor Module",
        inventory_coverage_days=Decimal("14"),
        typical_lead_time_days=Decimal("60"),
        recovery_duration_days=Decimal("30"),
        daily_downtime_cost_usd=Decimal("50000"),
        criticality="high",
    )
    res = calculate_operational_exposure(part)
    assert res.expected_decision_losses is not None
    losses = res.expected_decision_losses
    assert losses["status"] == "computed"
    assert "optimal_action_under_loss" in losses
    assert losses["daily_downtime_cost_usd"] == 50000.0

    actions = losses["actions"]
    assert "monitor" in actions
    assert "review_contingency_plan" in actions
    assert "activate_secondary_source" in actions


def test_exposure_uncalibrated_sensitivity_when_cost_absent() -> None:
    part = PartExposureInput(
        part_name="Standard Sensor Module",
        inventory_coverage_days=Decimal("14"),
        typical_lead_time_days=Decimal("60"),
        recovery_duration_days=Decimal("30"),
        daily_downtime_cost_usd=None,  # No financial input
    )
    res = calculate_operational_exposure(part)
    assert res.expected_decision_losses is None
    assert res.sensitivity_analysis["status"] == "illustrative_sensitivity"
    assert res.sensitivity_analysis["gap_days"] == 16.0
    assert "$50,000/day" in res.sensitivity_analysis["estimated_loss_at_rates_usd"]
