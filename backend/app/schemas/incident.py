"""
Pydantic schemas for IncidentCandidate and ExposureAssessment.

Evidence status and exposure bands are explicit enumerations.
independent_support_count is nullable — never assumed from URL count.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.decision import PolicyDecisionRead


class ExposureInputValue(BaseModel):
    """One input to the exposure calculation with provenance."""

    value: Decimal | None = None
    provenance: Literal["user_input", "source_evidence", "scenario_assumption", "unknown"]
    source_id: str | None = None  # if provenance is source_evidence
    note: str | None = None


class ExposureAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    input_values_json: dict
    calculation_name: str
    calculation_version: str
    # Null means unknown — never replaced with zero
    potential_inventory_gap_days: Decimal | None = None
    criticality: Literal["low", "medium", "high", "unknown"]
    alternative_available: Literal["yes", "no", "unknown"]
    exposure_band: Literal["low", "moderate", "high", "unknown"]
    assumptions: list[str]
    limitations: list[str]
    created_at: datetime


class IncidentCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    supplier_id: str | None = None
    event_type: str | None = None
    facility_location: str | None = None
    event_date_start: str | None = None
    event_date_end: str | None = None
    claim_ids: list[str]
    entity_match_status: Literal["confirmed", "probable", "ambiguous", "mismatch", "unknown"]
    evidence_status: Literal[
        "primary_source_reported",
        "corroborated",
        "single_source",
        "disputed",
        "unverified",
        "outdated_or_resolved",
        "false_entity_match",
        "unknown",
    ]
    # Null unless lineage evidence supports a defensible conclusion
    reporting_group_count: int | None = None
    independent_support_count: int | None = None
    contradiction_summary: str | None = None
    review_required: bool
    exposure: ExposureAssessmentRead | None = None
    policy_decision: PolicyDecisionRead | None = None
    created_at: datetime
    updated_at: datetime
