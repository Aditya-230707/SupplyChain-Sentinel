"""
Pydantic schemas for Claim — structured LLM-extracted facts.

A Claim is what a source says, not automatically true.
Extraction status and quote validation are always explicit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    source_id: str
    subject_text: str
    subject_candidate_supplier_id: str | None = None
    event_type: str | None = None
    object_text: str | None = None
    event_date: str | None = None
    event_date_precision: Literal["day", "month", "year", "unknown"] = "unknown"
    location_text: str | None = None
    claim_type: Literal[
        "incident",
        "impact",
        "response",
        "allegation",
        "official_finding",
        "resolution",
        "correction",
        "other",
    ]
    polarity: Literal["supports", "contradicts", "contextual", "unknown"]
    supporting_quote: str | None = None
    quote_start: int | None = None
    quote_end: int | None = None
    extraction_status: Literal["validated", "quote_mismatch", "schema_invalid", "needs_review"]
    evidence_limitations: list[str]
    model_run_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ExtractedClaimItem(BaseModel):
    """A claim extracted by the LLM from source text."""

    subject_text: str
    event_type: Literal[
        "operational_disruption",
        "environmental_regulatory",
        "logistics_disruption",
        "other",
    ] = "other"
    object_text: str
    event_date: str | None = None
    event_date_precision: Literal["day", "month", "year", "unknown"] = "unknown"
    location_text: str | None = None
    claim_type: Literal[
        "incident",
        "impact",
        "response",
        "allegation",
        "official_finding",
        "resolution",
        "correction",
        "other",
    ] = "incident"
    polarity: Literal["supports", "contradicts", "contextual", "unknown"] = "supports"
    supporting_quote: str
    evidence_limitations: list[str] = []


class ClaimExtractionResponse(BaseModel):
    """The root structured response required from the LLM for claim extraction."""

    claims: list[ExtractedClaimItem] = []
    summary: str | None = None
