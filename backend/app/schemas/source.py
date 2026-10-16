"""
Pydantic schemas for SourceDocument and SourceRelation.

Source content is always untrusted data; never executed or injected into prompts
as instructions. Content status is always explicit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventDateCandidate(BaseModel):
    """A candidate event date with provenance information."""

    date_text: str  # raw text from source
    date_iso: str | None = None  # ISO-8601 if parseable
    precision: Literal["day", "month", "year", "unknown"] = "unknown"
    # claim | publication_proxy | model_extraction
    provenance: str = "model_extraction"


class SourceDocumentBase(BaseModel):
    url_original: str = Field(..., description="Original URL as returned by search provider")
    url_canonical: str = Field(..., description="Normalized/canonical URL")
    title: str | None = None
    publisher_name: str | None = None
    domain: str | None = None
    published_at: datetime | None = None
    event_date_candidates: list[EventDateCandidate] = Field(default_factory=list)
    content_excerpt: str | None = None
    content_hash: str | None = None
    provider_result_id: str | None = None
    source_class: Literal[
        "official_primary",
        "company_statement",
        "established_media",
        "specialist_media",
        "other",
        "unknown",
    ] = "unknown"
    content_status: Literal["available", "snippet_only", "inaccessible", "extraction_failed"] = (
        "snippet_only"
    )
    license_or_usage_notes: str | None = None


class SourceDocumentRead(SourceDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    retrieved_at: datetime
    created_at: datetime


class SourceRelationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_a_id: str
    source_b_id: str
    relation: Literal[
        "same_url",
        "exact_duplicate",
        "near_duplicate",
        "syndicated",
        "cites_same_origin",
        "possible_derivative",
        "unknown",
    ]
    evidence: dict
    review_status: Literal["automatic_candidate", "human_confirmed", "human_rejected"]
    created_at: datetime
