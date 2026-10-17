"""
Operational exposure & mathematical decision loss module.

Implements Rules:
- EX-001: Part relationship required for operational relevance.
- EX-002: Missing duration or coverage yields null, never zero (null-safety).
- EX-003: Deterministic point gap: gap_days = max(0, duration_days - inventory_coverage_days).
- EX-004: Range propagation: [D_min, D_max] -> [gap_min, gap_max].
- EX-005: Deterministic scenario evaluation: Short interruption, Baseline, Extended disruption.
- EX-006: Expected loss calculation: expected_loss(action) = sum(P(s) * Loss(action, s))
          when daily downtime cost is documented.
- EX-007: Uncalibrated sensitivity analysis when financial inputs are absent.
- EX-008: Explicit provenance tracking for all inputs (observed vs user vs assumed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class PartExposureInput:
    part_name: str
    inventory_coverage_days: Decimal | None
    typical_lead_time_days: Decimal | None
    recovery_duration_days: Decimal | None
    recovery_duration_min_days: Decimal | None = None
    recovery_duration_max_days: Decimal | None = None
    daily_downtime_cost_usd: Decimal | None = None  # user/ERP supplied
    alternative_available: str = "unknown"  # yes | no | unknown
    criticality: str = "unknown"  # low | medium | high | unknown
    recovery_provenance: str = (
        "unknown"  # source_evidence | user_input | scenario_assumption | unknown
    )


@dataclass
class ExposureResult:
    potential_inventory_gap_days: Decimal | None
    exposure_band: str  # low | moderate | high | unknown
    criticality: str
    alternative_available: str
    calculation_name: str
    calculation_version: str
    input_values: dict[str, Any]
    potential_inventory_gap_min_days: Decimal | None = None
    potential_inventory_gap_max_days: Decimal | None = None
    scenarios: list[dict[str, Any]] = field(default_factory=list)
    expected_decision_losses: dict[str, Any] | None = None
    sensitivity_analysis: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


def calculate_operational_exposure(
    part: PartExposureInput | None,
    evidenced_disruption_days: Decimal | None = None,
    evidenced_disruption_min_days: Decimal | None = None,
    evidenced_disruption_max_days: Decimal | None = None,
) -> ExposureResult:
    """Calculate potential inventory gap days, range propagation, and scenario losses.

    Rules:
    - If part or duration/coverage is missing, gap is None, never 0.
    - gap = max(0, disruption_days - coverage_days).
    - [D_min, D_max] bounds propagate to [gap_min, gap_max].
    """
    if part is None:
        return ExposureResult(
            potential_inventory_gap_days=None,
            potential_inventory_gap_min_days=None,
            potential_inventory_gap_max_days=None,
            exposure_band="unknown",
            criticality="unknown",
            alternative_available="unknown",
            calculation_name="inventory_gap_v2",
            calculation_version="2.0",
            input_values={},
            scenarios=[],
            expected_decision_losses=None,
            sensitivity_analysis={},
            assumptions=[],
            limitations=["EX-001: No part/operational relationship established for supplier."],
        )

    # Determine disruption duration (point, min, max)
    duration: Decimal | None = (
        evidenced_disruption_days
        if evidenced_disruption_days is not None
        else part.recovery_duration_days
    )
    duration_min: Decimal | None = (
        evidenced_disruption_min_days
        if evidenced_disruption_min_days is not None
        else part.recovery_duration_min_days
    )
    duration_max: Decimal | None = (
        evidenced_disruption_max_days
        if evidenced_disruption_max_days is not None
        else part.recovery_duration_max_days
    )

    duration_provenance = (
        "source_evidence" if evidenced_disruption_days is not None else part.recovery_provenance
    )

    inputs_snapshot: dict[str, Any] = {
        "part_name": part.part_name,
        "inventory_coverage_days": {
            "value": float(part.inventory_coverage_days)
            if part.inventory_coverage_days is not None
            else None,
            "provenance": "user_input" if part.inventory_coverage_days is not None else "unknown",
        },
        "disruption_duration_days": {
            "value": float(duration) if duration is not None else None,
            "min_value": float(duration_min) if duration_min is not None else None,
            "max_value": float(duration_max) if duration_max is not None else None,
            "provenance": duration_provenance,
        },
        "typical_lead_time_days": {
            "value": float(part.typical_lead_time_days)
            if part.typical_lead_time_days is not None
            else None,
            "provenance": "user_input" if part.typical_lead_time_days is not None else "unknown",
        },
        "daily_downtime_cost_usd": {
            "value": float(part.daily_downtime_cost_usd)
            if part.daily_downtime_cost_usd is not None
            else None,
            "provenance": "user_input" if part.daily_downtime_cost_usd is not None else "unknown",
        },
        "criticality": part.criticality,
        "alternative_available": part.alternative_available,
    }

    assumptions: list[str] = []
    limitations: list[str] = []

    # EX-002: Null-safe handling when duration or inventory is unknown
    if duration is None or part.inventory_coverage_days is None:
        if duration is None:
            limitations.append(
                "Disruption duration is unknown. Inventory gap cannot be computed without guessing."
            )
        if part.inventory_coverage_days is None:
            limitations.append(
                "Inventory coverage days is unknown in master data. "
                "Inventory gap cannot be computed."
            )

        return ExposureResult(
            potential_inventory_gap_days=None,
            potential_inventory_gap_min_days=None,
            potential_inventory_gap_max_days=None,
            exposure_band="unknown",
            criticality=part.criticality,
            alternative_available=part.alternative_available,
            calculation_name="inventory_gap_v2",
            calculation_version="2.0",
            input_values=inputs_snapshot,
            scenarios=[],
            expected_decision_losses=None,
            sensitivity_analysis={},
            assumptions=assumptions,
            limitations=limitations,
        )

    # EX-003: Point Gap formula: gap = max(0, duration - inventory)
    cov_dec = Decimal(str(part.inventory_coverage_days))
    dur_dec = Decimal(str(duration))
    gap = max(Decimal("0"), dur_dec - cov_dec)

    # EX-004: Range Propagation: [gap_min, gap_max]
    gap_min: Decimal | None = None
    gap_max: Decimal | None = None
    if duration_min is not None:
        gap_min = max(Decimal("0"), Decimal(str(duration_min)) - cov_dec)
    if duration_max is not None:
        gap_max = max(Decimal("0"), Decimal(str(duration_max)) - cov_dec)

    # Exposure band determination
    if gap == Decimal("0"):
        exposure_band = "low"
    elif gap <= Decimal("14"):
        exposure_band = "moderate"
    else:
        exposure_band = "high"

    if part.criticality == "high" and gap > Decimal("0"):
        exposure_band = "high"
        assumptions.append("Exposure band escalated to 'high' because part criticality is high.")

    # EX-005: Scenario Projections
    scenarios: list[dict[str, Any]] = [
        {
            "name": "Short Interruption",
            "description": "Rapid containment; operations resume within 7 days or minor pause.",
            "duration_days": 7.0,
            "inventory_gap_days": float(max(Decimal("0"), Decimal("7") - cov_dec)),
            "depletion_avoided": cov_dec >= Decimal("7"),
            "probability_assumption": 0.25,
        },
        {
            "name": "Baseline Grounded",
            "description": (
                f"Incident duration aligns with extracted evidence ({float(dur_dec)} days)."
            ),
            "duration_days": float(dur_dec),
            "inventory_gap_days": float(gap),
            "depletion_avoided": gap == Decimal("0"),
            "probability_assumption": 0.55,
        },
        {
            "name": "Extended Disruption",
            "description": "Secondary damage or supply bottleneck extends downtime by 50%.",
            "duration_days": float(round(dur_dec * Decimal("1.5"), 1)),
            "inventory_gap_days": float(
                max(Decimal("0"), round(dur_dec * Decimal("1.5"), 1) - cov_dec)
            ),
            "depletion_avoided": False,
            "probability_assumption": 0.20,
        },
    ]

    # EX-006 & EX-007: Expected Decision Loss or Sensitivity Analysis
    expected_decision_losses: dict[str, Any] | None = None
    sensitivity_analysis: dict[str, Any] = {}

    # Action parameters: (action_cost, mitigation_factor)
    actions = {
        "monitor": {
            "cost": 0.0,
            "mitigation": 0.0,
            "description": "Passive monitoring; zero upfront spend",
        },
        "request_supplier_confirmation": {
            "cost": 500.0,
            "mitigation": 0.15,
            "description": "Direct inquiry; confirms recovery timeline and expedited lots",
        },
        "review_contingency_plan": {
            "cost": 2500.0,
            "mitigation": 0.40,
            "description": "Reserve freight capacity and evaluate buffer inventory reallocation",
        },
        "activate_secondary_source": {
            "cost": 15000.0,
            "mitigation": 0.85,
            "description": "Place pre-emptive tooling or expedite order with alternative supplier",
        },
    }

    if part.daily_downtime_cost_usd is not None:
        d_cost = float(part.daily_downtime_cost_usd)
        losses_by_action: dict[str, Any] = {}

        for act_name, act_props in actions.items():
            fixed_cost = act_props["cost"]
            mitigation = act_props["mitigation"]
            expected_loss = fixed_cost

            scenario_breakdowns = []
            for sc in scenarios:
                raw_gap_loss = sc["inventory_gap_days"] * d_cost
                mitigated_loss = raw_gap_loss * (1.0 - mitigation)
                prob = sc["probability_assumption"]
                expected_loss += prob * mitigated_loss
                scenario_breakdowns.append(
                    {
                        "scenario": sc["name"],
                        "raw_gap_loss_usd": round(raw_gap_loss, 2),
                        "mitigated_loss_usd": round(mitigated_loss, 2),
                        "weighted_loss_usd": round(prob * mitigated_loss, 2),
                    }
                )

            losses_by_action[act_name] = {
                "fixed_action_cost_usd": fixed_cost,
                "mitigation_rate": mitigation,
                "expected_total_loss_usd": round(expected_loss, 2),
                "scenario_breakdown": scenario_breakdowns,
            }

        # Find mathematically optimal action under expected loss
        best_action = min(
            losses_by_action.keys(), key=lambda k: losses_by_action[k]["expected_total_loss_usd"]
        )
        expected_decision_losses = {
            "status": "computed",
            "daily_downtime_cost_usd": d_cost,
            "optimal_action_under_loss": best_action,
            "actions": losses_by_action,
        }
    else:
        # EX-007: Uncalibrated sensitivity analysis
        limitations.append(
            "Daily downtime cost (USD) not provided in part master data. "
            "Financial loss cannot be calculated."
        )
        hypothetical_daily_rates = [10_000.0, 50_000.0, 100_000.0]
        sensitivity_analysis = {
            "status": "illustrative_sensitivity",
            "gap_days": float(gap),
            "hypothetical_daily_rates_usd": hypothetical_daily_rates,
            "estimated_loss_at_rates_usd": {
                f"${int(rate):,}/day": round(float(gap) * rate, 2)
                for rate in hypothetical_daily_rates
            },
            "disclaimer": "Illustrative sensitivity only. Not calibrated financial risk.",
        }

    return ExposureResult(
        potential_inventory_gap_days=gap,
        potential_inventory_gap_min_days=gap_min,
        potential_inventory_gap_max_days=gap_max,
        exposure_band=exposure_band,
        criticality=part.criticality,
        alternative_available=part.alternative_available,
        calculation_name="inventory_gap_v2",
        calculation_version="2.0",
        input_values=inputs_snapshot,
        scenarios=scenarios,
        expected_decision_losses=expected_decision_losses,
        sensitivity_analysis=sensitivity_analysis,
        assumptions=assumptions,
        limitations=limitations,
    )
