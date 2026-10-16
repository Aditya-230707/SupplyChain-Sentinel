"""
SQLAlchemy 2.x ORM models for SupplyChain Sentinel.

Design notes:
- UUIDs as primary keys (stored as TEXT in SQLite, UUID in PostgreSQL).
- All timestamps are UTC; conversion to local time happens only in the UI.
- JSON columns use SQLAlchemy's JSON type (TEXT in SQLite, JSONB in PostgreSQL).
- Audit records are append-only; corrections create new records.
- No model field represents a probability or calibrated confidence score.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON as SA_JSON
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass  # avoid circular imports; use string annotations for relationships


from datetime import UTC


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# ---- Enums (as string literals stored in DB) -----------------
# Using Python Literal types for Pydantic; stored as VARCHAR in DB.


class Supplier(Base):
    """A known supplier entity with identity signals."""

    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    # Stored as JSON array of strings
    aliases: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    official_domains: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    registry_ids: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    country_or_region: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # low | medium | high | unknown
    criticality: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now, nullable=False
    )

    # Relationships
    parts: Mapped[list[SupplierPart]] = relationship(
        "SupplierPart", back_populates="supplier", cascade="all, delete-orphan", lazy="selectin"
    )
    investigations: Mapped[list[InvestigationRun]] = relationship(
        "InvestigationRun", back_populates="supplier"
    )

    __table_args__ = (Index("ix_suppliers_name_active", "name", "active"),)


class SupplierPart(Base):
    """A part/component supplied by a Supplier, with operational context."""

    __tablename__ = "supplier_parts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    part_name: Mapped[str] = mapped_column(String(500), nullable=False)
    part_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Stored as Decimal (NUMERIC in DB); null means unknown
    inventory_coverage_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    typical_lead_time_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Optional — user or evidence provided; never hallucinated
    recovery_duration_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # yes | no | unknown
    alternative_supplier_available: Mapped[str] = mapped_column(
        String(10), default="unknown", nullable=False
    )
    business_unit: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # user_input | imported_file | source_evidence
    relationship_source: Mapped[str] = mapped_column(
        String(30), default="user_input", nullable=False
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now, nullable=False
    )

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="parts")


class InvestigationRun(Base):
    """One investigation of a supplier — tracks pipeline status and metadata."""

    __tablename__ = "investigation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id"), nullable=False, index=True
    )
    # queued | searching | extracting | resolving | adjudicating |
    # assessing_impact | composing | completed | completed_with_warnings | failed
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    requested_categories: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    pipeline_version: Mapped[str] = mapped_column(String(50), default="0.1.0", nullable=False)
    # {"claim_extraction": "v1", "brief_composition": "v1"}
    prompt_versions: Mapped[dict] = mapped_column(SA_JSON, default=dict, nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Safe metrics only (no secrets, no full payloads)
    metrics_json: Mapped[dict] = mapped_column(SA_JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now, nullable=False
    )

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="investigations")
    sources: Mapped[list[SourceDocument]] = relationship(
        "SourceDocument", back_populates="investigation", cascade="all, delete-orphan"
    )
    claims: Mapped[list[Claim]] = relationship(
        "Claim", back_populates="investigation", cascade="all, delete-orphan"
    )
    incidents: Mapped[list[IncidentCandidate]] = relationship(
        "IncidentCandidate", back_populates="investigation", cascade="all, delete-orphan"
    )
    model_runs: Mapped[list[ModelRun]] = relationship(
        "ModelRun", back_populates="investigation", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_investigation_runs_supplier_status", "supplier_id", "status"),)


class SourceDocument(Base):
    """A retrieved source (article, regulatory notice, press release, etc.)."""

    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url_original: Mapped[str] = mapped_column(Text, nullable=False)
    url_canonical: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    # Structured event date candidates with provenance
    event_date_candidates: Mapped[list[dict]] = mapped_column(SA_JSON, default=list, nullable=False)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    provider_result_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # official_primary | company_statement | established_media | specialist_media | other | unknown
    source_class: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    # available | snippet_only | inaccessible | extraction_failed
    content_status: Mapped[str] = mapped_column(String(30), default="snippet_only", nullable=False)
    license_or_usage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )

    investigation: Mapped[InvestigationRun] = relationship(
        "InvestigationRun", back_populates="sources"
    )
    claims: Mapped[list[Claim]] = relationship("Claim", back_populates="source")

    __table_args__ = (
        Index("ix_source_documents_investigation_canonical", "investigation_id", "url_canonical"),
    )


class SourceRelation(Base):
    """A candidate relationship between two SourceDocuments (e.g. duplicate, derivative)."""

    __tablename__ = "source_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_a_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False
    )
    source_b_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False
    )
    # same_url | exact_duplicate | near_duplicate | syndicated |
    # cites_same_origin | possible_derivative | unknown
    relation: Mapped[str] = mapped_column(String(40), nullable=False)
    # Rule and observations used to detect
    evidence: Mapped[dict] = mapped_column(SA_JSON, default=dict, nullable=False)
    # automatic_candidate | human_confirmed | human_rejected
    review_status: Mapped[str] = mapped_column(
        String(30), default="automatic_candidate", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )


class Claim(Base):
    """A structured claim extracted by the LLM from a SourceDocument.

    A Claim represents what a source *says*, not automatically the truth.
    Quote must be validated against stored source content before being used.
    """

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Entity wording exactly as described in the source
    subject_text: Mapped[str] = mapped_column(Text, nullable=False)
    # FK to supplier if resolution succeeded; nullable until resolved
    subject_candidate_supplier_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("suppliers.id"), nullable=True
    )
    # e.g. operational_disruption | environmental_regulatory | logistics_disruption
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    object_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[str | None] = mapped_column(String(30), nullable=True)  # ISO date string
    # day | month | year | unknown
    event_date_precision: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    location_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # incident | impact | response | allegation | official_finding | resolution | correction | other
    claim_type: Mapped[str] = mapped_column(String(40), default="incident", nullable=False)
    # supports | contradicts | contextual | unknown
    polarity: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    # Exact quote substring from stored source text
    supporting_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quote_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # validated | quote_mismatch | schema_invalid | needs_review
    extraction_status: Mapped[str] = mapped_column(
        String(30), default="needs_review", nullable=False
    )
    evidence_limitations: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    model_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("model_runs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now, nullable=False
    )

    investigation: Mapped[InvestigationRun] = relationship(
        "InvestigationRun", back_populates="claims"
    )
    source: Mapped[SourceDocument] = relationship("SourceDocument", back_populates="claims")


class IncidentCandidate(Base):
    """A clustered group of claims that appear to describe the same event."""

    __tablename__ = "incident_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable if supplier identity is ambiguous/unknown
    supplier_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("suppliers.id"), nullable=True
    )
    # e.g. operational_disruption
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    facility_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date_start: Mapped[str | None] = mapped_column(String(30), nullable=True)
    event_date_end: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # claim IDs as JSON array of strings
    claim_ids: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    # confirmed | probable | ambiguous | mismatch | unknown
    entity_match_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    # primary_source_reported | corroborated | single_source | disputed |
    # unverified | outdated_or_resolved | false_entity_match | unknown
    evidence_status: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    # Only set when lineage evidence supports it; never assumed from URL count
    reporting_group_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    independent_support_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contradiction_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now, nullable=False
    )

    investigation: Mapped[InvestigationRun] = relationship(
        "InvestigationRun", back_populates="incidents"
    )
    exposure: Mapped[ExposureAssessment | None] = relationship(
        "ExposureAssessment", back_populates="incident", uselist=False, lazy="selectin"
    )
    policy_decision: Mapped[PolicyDecision | None] = relationship(
        "PolicyDecision", back_populates="incident", uselist=False, lazy="selectin"
    )


class ExposureAssessment(Base):
    """Deterministic operational exposure calculation for an IncidentCandidate.

    All inputs include provenance. Null means unknown — never assumed to be zero.
    """

    __tablename__ = "exposure_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_candidates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # {"inventory_coverage_days": {"value": 30, "provenance": "user_input"}, ...}
    input_values_json: Mapped[dict] = mapped_column(SA_JSON, default=dict, nullable=False)
    calculation_name: Mapped[str] = mapped_column(String(100), default="inventory_gap_v1")
    calculation_version: Mapped[str] = mapped_column(String(20), default="1.0")
    # null if either input is unknown; never replaced with zero
    potential_inventory_gap_days: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    criticality: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    # yes | no | unknown
    alternative_available: Mapped[str] = mapped_column(
        String(10), default="unknown", nullable=False
    )
    # low | moderate | high | unknown
    exposure_band: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    assumptions: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )

    incident: Mapped[IncidentCandidate] = relationship(
        "IncidentCandidate", back_populates="exposure"
    )


class PolicyDecision(Base):
    """Output of the deterministic policy engine for an IncidentCandidate.

    Rules are evaluated in deterministic order; no LLM involvement.
    """

    __tablename__ = "policy_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_candidates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    # monitor | request_supplier_confirmation | review_contingency_plan |
    # urgent_human_review | insufficient_evidence
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_ids_fired: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(SA_JSON, default=dict, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    blockers: Mapped[list[str]] = mapped_column(SA_JSON, default=list, nullable=False)
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )

    incident: Mapped[IncidentCandidate] = relationship(
        "IncidentCandidate", back_populates="policy_decision"
    )
    human_reviews: Mapped[list[HumanReview]] = relationship(
        "HumanReview", back_populates="policy_decision"
    )


class HumanReview(Base):
    """A human reviewer action on a PolicyDecision."""

    __tablename__ = "human_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    policy_decision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policy_decisions.id"), nullable=False, index=True
    )
    # approve_recommendation | reject_recommendation |
    # request_more_information | mark_monitor_only
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    override_recommendation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reviewer_name: Mapped[str | None] = mapped_column(
        String(100), default="Procurement Reviewer", nullable=True
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    # version of policy decision at review time
    prior_recommendation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )

    policy_decision: Mapped[PolicyDecision] = relationship(
        "PolicyDecision", back_populates="human_reviews"
    )


class AuditEvent(Base):
    """Append-only log of significant system and human actions.

    Records are never deleted; corrections create new records.
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # investigation_run | supplier | evidence_status | policy_config |
    # recommendation | human_disposition
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    # Safe data only — no secrets, no full model payloads
    data: Mapped[dict] = mapped_column(SA_JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False, index=True
    )


class ModelRun(Base):
    """Record of one LLM inference call — for audit and cost tracking."""

    __tablename__ = "model_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigation_runs.id", ondelete="CASCADE"), nullable=False
    )
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # ok | schema_invalid | quote_mismatch | provider_error | timeout
    status: Mapped[str] = mapped_column(String(30), default="ok", nullable=False)
    validation_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_prompt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, nullable=False
    )

    investigation: Mapped[InvestigationRun] = relationship(
        "InvestigationRun", back_populates="model_runs"
    )
