"""
Human Review & Audit API endpoints.

Endpoints:
- POST /api/v1/incidents/{incident_id}/decision — record human reviewer disposition
- GET  /api/v1/incidents/{incident_id}/reviews  — list human reviews for an incident
- GET  /api/v1/audit-events                     — list immutable audit trail events
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.db.models import (
    AuditEvent as AuditEventModel,
)
from app.db.models import (
    HumanReview as HumanReviewModel,
)
from app.db.models import (
    IncidentCandidate as IncidentCandidateModel,
)
from app.db.session import get_db_session
from app.schemas.decision import (
    AuditEventRead,
    HumanReviewCreate,
    HumanReviewRead,
)

log = structlog.get_logger(__name__)
router = APIRouter(tags=["reviews"])


@router.post(
    "/incidents/{incident_id}/decision",
    response_model=HumanReviewRead,
    status_code=201,
)
async def record_human_decision(
    incident_id: str,
    payload: HumanReviewCreate,
    db: AsyncSession = Depends(get_db_session),
) -> HumanReviewRead:
    """Record a human reviewer's disposition on an automated policy recommendation.

    - Overriding or rejecting the recommendation requires a non-empty reviewer note.
    - Preserves the prior recommendation and all underlying evidence immutably.
    - Appends a 'human_disposition' record to the audit trail.
    """
    stmt = (
        select(IncidentCandidateModel)
        .options(selectinload(IncidentCandidateModel.policy_decision))
        .where(IncidentCandidateModel.id == incident_id)
    )
    incident = (await db.execute(stmt)).scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")

    if not incident.policy_decision:
        raise ValidationError(f"Incident {incident_id} does not have an evaluated policy decision")

    # Require note when overriding or rejecting
    is_override = payload.action in ("reject_recommendation", "mark_monitor_only") or (
        payload.override_recommendation
        and payload.override_recommendation != incident.policy_decision.recommendation
    )
    if is_override and (not payload.reviewer_note or len(payload.reviewer_note.strip()) < 5):
        raise ValidationError(
            "An explicit reviewer rationale (at least 5 characters) is required "
            "when rejecting or overriding an automated policy recommendation."
        )

    now = datetime.now(UTC)
    review = HumanReviewModel(
        policy_decision_id=incident.policy_decision.id,
        action=payload.action,
        override_recommendation=payload.override_recommendation,
        reviewer_name=payload.reviewer_name or "Procurement Reviewer",
        reviewer_note=payload.reviewer_note.strip() if payload.reviewer_note else None,
        reviewed_at=now,
        prior_recommendation=incident.policy_decision.recommendation,
    )
    db.add(review)

    # Update incident review flag: decision has been made
    incident.review_required = False

    # Append immutable audit event
    audit_data = {
        "action": payload.action,
        "prior_recommendation": incident.policy_decision.recommendation,
        "override_recommendation": payload.override_recommendation,
        "reviewer_name": payload.reviewer_name or "Procurement Reviewer",
        "reviewer_note": payload.reviewer_note.strip() if payload.reviewer_note else None,
        "investigation_id": incident.investigation_id,
        "policy_decision_id": incident.policy_decision.id,
    }
    audit_event = AuditEventModel(
        event_type="human_disposition",
        entity_type="incident_candidate",
        entity_id=incident.id,
        data=audit_data,
        created_at=now,
    )
    db.add(audit_event)

    await db.commit()
    await db.refresh(review)

    log.info(
        "human_decision_recorded",
        incident_id=incident.id,
        action=payload.action,
        override=payload.override_recommendation,
    )
    return HumanReviewRead.model_validate(review)


@router.get(
    "/incidents/{incident_id}/reviews",
    response_model=list[HumanReviewRead],
)
async def get_incident_reviews(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[HumanReviewRead]:
    """Get all human review records for an incident."""
    stmt = (
        select(IncidentCandidateModel)
        .options(selectinload(IncidentCandidateModel.policy_decision))
        .where(IncidentCandidateModel.id == incident_id)
    )
    incident = (await db.execute(stmt)).scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")

    if not incident.policy_decision:
        return []

    rev_stmt = (
        select(HumanReviewModel)
        .where(HumanReviewModel.policy_decision_id == incident.policy_decision.id)
        .order_by(HumanReviewModel.reviewed_at.desc())
    )
    rows = (await db.execute(rev_stmt)).scalars().all()
    return [HumanReviewRead.model_validate(r) for r in rows]


@router.get(
    "/audit-events",
    response_model=list[AuditEventRead],
)
async def list_audit_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> list[AuditEventRead]:
    """List immutable audit log events in descending order."""
    stmt = select(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [AuditEventRead.model_validate(r) for r in rows]
