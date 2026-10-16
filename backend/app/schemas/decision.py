"""
Pydantic schemas for PolicyDecision and HumanReview.

Policy engine output is deterministic; recommendation enums are explicit.
Human review records preserve prior recommendation for audit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PolicyRecommendation = Literal[
    "monitor",
    "request_supplier_confirmation",
    "review_contingency_plan",
    "urgent_human_review",
    "insufficient_evidence",
]

HumanReviewAction = Literal[
    "approve_recommendation",
    "reject_recommendation",
    "request_more_information",
    "mark_monitor_only",
]


class PolicyDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    policy_version: str
    recommendation: PolicyRecommendation
    rule_ids_fired: list[str]
    input_snapshot: dict
    reasons: list[str]
    blockers: list[str]
    human_review_required: bool
    created_at: datetime


class HumanReviewCreate(BaseModel):
    action: HumanReviewAction
    reviewer_note: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional rationale or correction note from the reviewer",
    )


class HumanReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    policy_decision_id: str
    action: HumanReviewAction
    reviewer_note: str | None = None
    reviewed_at: datetime
    prior_recommendation: str | None = None
    created_at: datetime


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    data: dict
    created_at: datetime
