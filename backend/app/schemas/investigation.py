"""
Pydantic schemas for InvestigationRun — create, status polling, and full read.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VALID_CATEGORIES = frozenset(
    [
        "operational_disruption",
        "environmental_regulatory",
        "logistics_disruption",
    ]
)

InvestigationStatus = Literal[
    "queued",
    "searching",
    "extracting",
    "resolving",
    "adjudicating",
    "assessing_impact",
    "composing",
    "completed",
    "completed_with_warnings",
    "failed",
]


class InvestigationCreate(BaseModel):
    supplier_id: str = Field(..., description="UUID of an existing active supplier")
    requested_categories: list[str] = Field(
        default_factory=lambda: list(VALID_CATEGORIES),
        description="Incident categories to investigate. Must be from the allowlist.",
    )
    date_range_start: str | None = Field(
        default=None,
        description="ISO date string — search results before this date are deprioritized",
    )
    date_range_end: str | None = None
    search_mode: Literal["fixture", "live"] = Field(
        default="fixture",
        description="Search mode: 'fixture' for demo, 'live' for Tavily",
    )

    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_CATEGORIES
        if invalid:
            msg = f"Unknown categories: {invalid}. Valid: {VALID_CATEGORIES}"
            raise ValueError(msg)
        if not v:
            msg = "At least one category is required"
            raise ValueError(msg)
        return v


class InvestigationStatusResponse(BaseModel):
    """Lightweight status response for polling."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    supplier_id: str
    status: InvestigationStatus
    requested_categories: list[str]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    pipeline_version: str
    provider_name: str | None = None
    model_name: str | None = None
    error_code: str | None = None
    error_summary: str | None = None
    metrics_json: dict
    created_at: datetime
    updated_at: datetime


class InvestigationCreateResponse(BaseModel):
    """Returned immediately after submitting an investigation."""

    id: str
    supplier_id: str
    status: InvestigationStatus
    created_at: datetime
