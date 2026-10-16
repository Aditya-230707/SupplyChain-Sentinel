"""
Operational exposure calculation module.

Implements Rules:
- EX-001: Part relationship required for relevance.
- EX-002: Missing duration or coverage yields null, never zero.
- EX-003: gap_days = max(0, duration_days - inventory_coverage_days).
- EX-004: Criticality / alternative supplier availability adjust urgency, not truth.
- EX-005: Severity, evidence status, and business exposure are non-interchangeable.
- EX-006: Explicit provenance tagging for all inputs.
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
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


def calculate_operational_exposure(
    part: PartExposureInput | None,
    evidenced_disruption_days: Decimal | None = None,
) -> ExposureResult:
    """Calculate potential inventory gap days and exposure band deterministically.

    Rules:
    - If part or duration/coverage is missing, gap is None, never 0.
    - gap = max(0, disruption_days - coverage_days).
    """
    if part is None:
        return ExposureResult(
            potential_inventory_gap_days=None,
            exposure_band="unknown",
            criticality="unknown",
            alternative_available="unknown",
            calculation_name="inventory_gap_v1",
            calculation_version="1.0",
            input_values={},
            assumptions=[],
            limitations=["EX-001: No part/operational relationship established for supplier."],
        )

    # Determine disruption duration: prefer evidenced duration, fallback to part recovery duration
    duration: Decimal | None = None
    duration_provenance = "unknown"

    if evidenced_disruption_days is not None:
        duration = evidenced_disruption_days
        duration_provenance = "source_evidence"
    elif part.recovery_duration_days is not None:
        duration = part.recovery_duration_days
        duration_provenance = part.recovery_provenance

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
            "provenance": duration_provenance,
        },
        "typical_lead_time_days": {
            "value": float(part.typical_lead_time_days)
            if part.typical_lead_time_days is not None
            else None,
            "provenance": "user_input" if part.typical_lead_time_days is not None else "unknown",
        },
        "criticality": part.criticality,
        "alternative_available": part.alternative_available,
    }

    assumptions: list[str] = []
    limitations: list[str] = []

    # EX-002: If either duration or coverage is missing, gap is null
    if duration is None or part.inventory_coverage_days is None:
        if duration is None:
            limitations.append("Disruption duration is unknown. Gap cannot be calculated.")
        if part.inventory_coverage_days is None:
            limitations.append("Inventory coverage is unknown. Gap cannot be calculated.")

        return ExposureResult(
            potential_inventory_gap_days=None,
            exposure_band="unknown",
            criticality=part.criticality,
            alternative_available=part.alternative_available,
            calculation_name="inventory_gap_v1",
            calculation_version="1.0",
            input_values=inputs_snapshot,
            assumptions=assumptions,
            limitations=limitations,
        )

    # EX-003: Formula gap = max(0, duration - coverage)
    dur_dec = Decimal(str(duration))
    cov_dec = Decimal(str(part.inventory_coverage_days))
    gap = max(Decimal("0"), dur_dec - cov_dec)

    if duration_provenance == "scenario_assumption":
        assumptions.append(f"Disruption duration ({duration} days) is a scenario assumption.")

    # Determine exposure band
    if gap == Decimal("0"):
        exposure_band = "low"
    elif gap <= Decimal("14"):
        exposure_band = "moderate"
    else:
        exposure_band = "high"

    # Criticality escalation (EX-004)
    if part.criticality == "high" and gap > Decimal("0"):
        exposure_band = "high"
        assumptions.append("Exposure band elevated to high due to high part criticality.")

    return ExposureResult(
        potential_inventory_gap_days=gap,
        exposure_band=exposure_band,
        criticality=part.criticality,
        alternative_available=part.alternative_available,
        calculation_name="inventory_gap_v1",
        calculation_version="1.0",
        input_values=inputs_snapshot,
        assumptions=assumptions,
        limitations=limitations,
    )
