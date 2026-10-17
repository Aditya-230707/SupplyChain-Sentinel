"""
Investigation API endpoints.

Endpoints:
- POST /api/v1/investigations
- GET  /api/v1/investigations/{run_id}
- GET  /api/v1/investigations/{run_id}/sources
- GET  /api/v1/investigations/{run_id}/claims
- GET  /api/v1/investigations/{run_id}/incidents
- GET  /api/v1/incidents/{incident_id}
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import NotFoundError, ProviderUnavailableError
from app.db.models import (
    Claim as ClaimModel,
)
from app.db.models import (
    IncidentCandidate as IncidentCandidateModel,
)
from app.db.models import (
    InvestigationRun as InvestigationRunModel,
)
from app.db.models import (
    SourceDocument as SourceDocumentModel,
)
from app.db.models import (
    SourceRelation as SourceRelationModel,
)
from app.db.models import (
    Supplier as SupplierModel,
)
from app.db.session import get_db_session
from app.pipeline.orchestrator import run_investigation
from app.providers.factory import get_llm_provider
from app.providers.fixture_search_provider import get_demo_fixture_providers
from app.providers.tavily_provider import make_tavily_providers_from_settings
from app.schemas.claim import ClaimRead
from app.schemas.incident import IncidentCandidateRead
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationCreateResponse,
    InvestigationStatusResponse,
)
from app.schemas.source import SourceDocumentRead, SourceRelationRead

log = structlog.get_logger(__name__)
router = APIRouter(tags=["investigations"])


@router.post("/investigations", response_model=InvestigationCreateResponse, status_code=201)
async def create_investigation(
    payload: InvestigationCreate,
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationCreateResponse:
    """Create and immediately execute an investigation for a supplier."""
    supplier = await db.get(SupplierModel, payload.supplier_id)
    if not supplier:
        raise NotFoundError(f"Supplier {payload.supplier_id} not found")

    search_mode = payload.search_mode
    if search_mode == "ddg":
        from app.providers.ddg_provider import make_ddg_providers

        search, content = make_ddg_providers()
    elif search_mode == "live":
        settings = get_settings()
        if not settings.tavily_api_key:
            raise ProviderUnavailableError(
                "TAVILY_API_KEY is not configured for live search mode. "
                "Set TAVILY_API_KEY in your environment or choose Fixture Search mode."
            )
        search, content = make_tavily_providers_from_settings()
    else:
        # Fixture mode: rich demo scenarios tailored to supplier name
        search, content = get_demo_fixture_providers(supplier.name)

    run = InvestigationRunModel(
        supplier_id=supplier.id,
        status="queued",
        requested_categories=payload.requested_categories,
        pipeline_version="0.1.0",
        prompt_versions={"claim_extraction": "v1"},
        metrics_json={"search_mode": search_mode},
    )
    db.add(run)
    await db.flush()

    llm = get_llm_provider()

    # Execute orchestrator
    run = await run_investigation(
        investigation_id=run.id,
        db=db,
        search_provider=search,
        content_provider=content,
        llm_provider=llm,
    )

    log.info("investigation_finished", run_id=run.id, status=run.status, search_mode=search_mode)
    return InvestigationCreateResponse(
        id=run.id,
        supplier_id=run.supplier_id,
        status=run.status,  # type: ignore[arg-type]
        created_at=run.created_at,
    )


@router.get("/investigations", response_model=list[InvestigationStatusResponse])
async def list_investigations(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> list[InvestigationStatusResponse]:
    """List recent investigation runs ordered by created_at descending."""
    stmt = (
        select(InvestigationRunModel).order_by(InvestigationRunModel.created_at.desc()).limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [InvestigationStatusResponse.model_validate(r) for r in rows]


@router.get("/investigations/{run_id}", response_model=InvestigationStatusResponse)
async def get_investigation(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationStatusResponse:
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")
    return InvestigationStatusResponse.model_validate(run)


@router.get("/investigations/{run_id}/sources", response_model=list[SourceDocumentRead])
async def get_investigation_sources(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[SourceDocumentRead]:
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")

    stmt = select(SourceDocumentModel).where(SourceDocumentModel.investigation_id == run_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [SourceDocumentRead.model_validate(r) for r in rows]


@router.get("/investigations/{run_id}/claims", response_model=list[ClaimRead])
async def get_investigation_claims(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[ClaimRead]:
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")

    stmt = select(ClaimModel).where(ClaimModel.investigation_id == run_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [ClaimRead.model_validate(r) for r in rows]


@router.get("/investigations/{run_id}/incidents", response_model=list[IncidentCandidateRead])
async def get_investigation_incidents(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[IncidentCandidateRead]:
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")

    stmt = (
        select(IncidentCandidateModel)
        .options(
            selectinload(IncidentCandidateModel.exposure),
            selectinload(IncidentCandidateModel.policy_decision),
        )
        .where(IncidentCandidateModel.investigation_id == run_id)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [IncidentCandidateRead.model_validate(r) for r in rows]


@router.get("/incidents/{incident_id}", response_model=IncidentCandidateRead)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> IncidentCandidateRead:
    stmt = (
        select(IncidentCandidateModel)
        .options(
            selectinload(IncidentCandidateModel.exposure),
            selectinload(IncidentCandidateModel.policy_decision),
        )
        .where(IncidentCandidateModel.id == incident_id)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise NotFoundError(f"Incident {incident_id} not found")
    return IncidentCandidateRead.model_validate(row)


@router.get("/incidents", response_model=list[IncidentCandidateRead])
async def list_incidents(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> list[IncidentCandidateRead]:
    """List all incident candidates across investigations."""
    stmt = (
        select(IncidentCandidateModel)
        .options(
            selectinload(IncidentCandidateModel.exposure),
            selectinload(IncidentCandidateModel.policy_decision),
        )
        .order_by(IncidentCandidateModel.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [IncidentCandidateRead.model_validate(r) for r in rows]


@router.get("/investigations/{run_id}/relations", response_model=list[SourceRelationRead])
async def get_investigation_relations(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[SourceRelationRead]:
    """Get lineage and duplicate/syndication relations between sources in an investigation."""
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")

    sources = (
        (
            await db.execute(
                select(SourceDocumentModel.id).where(SourceDocumentModel.investigation_id == run_id)
            )
        )
        .scalars()
        .all()
    )

    if not sources:
        return []

    stmt = select(SourceRelationModel).where(
        SourceRelationModel.source_a_id.in_(sources) | SourceRelationModel.source_b_id.in_(sources)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [SourceRelationRead.model_validate(r) for r in rows]


@router.get("/investigations/{run_id}/graph")
async def get_investigation_evidence_graph(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Get the full evidence provenance DAG and integrity metrics for an investigation."""
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")

    supplier = (
        await db.execute(
            select(SupplierModel)
            .options(
                selectinload(SupplierModel.parts),
                selectinload(SupplierModel.facilities),
            )
            .where(SupplierModel.id == run.supplier_id)
        )
    ).scalar_one_or_none()
    if not supplier:
        raise NotFoundError(f"Supplier {run.supplier_id} not found")

    sources = (
        (
            await db.execute(
                select(SourceDocumentModel).where(SourceDocumentModel.investigation_id == run_id)
            )
        )
        .scalars()
        .all()
    )
    claims = (
        (await db.execute(select(ClaimModel).where(ClaimModel.investigation_id == run_id)))
        .scalars()
        .all()
    )
    src_ids = [s.id for s in sources]
    source_rels: list[SourceRelationModel] = []
    if src_ids:
        source_rels = list(
            (
                await db.execute(
                    select(SourceRelationModel).where(
                        SourceRelationModel.source_a_id.in_(src_ids)
                        | SourceRelationModel.source_b_id.in_(src_ids)
                    )
                )
            )
            .scalars()
            .all()
        )

    incident = (
        (
            await db.execute(
                select(IncidentCandidateModel)
                .options(
                    selectinload(IncidentCandidateModel.exposure),
                    selectinload(IncidentCandidateModel.policy_decision),
                )
                .where(IncidentCandidateModel.investigation_id == run_id)
            )
        )
        .scalars()
        .first()
    )

    from app.pipeline.evidence_graph import build_investigation_evidence_graph

    graph = build_investigation_evidence_graph(
        supplier_data={
            "id": supplier.id,
            "name": supplier.name,
            "criticality": supplier.criticality,
            "country_or_region": supplier.country_or_region,
            "official_domains": supplier.official_domains,
        },
        facilities_data=[
            {
                "id": f.id,
                "facility_name": f.facility_name,
                "facility_type": f.facility_type,
                "city_or_address": f.city_or_address,
                "country_or_region": f.country_or_region,
            }
            for f in (supplier.facilities or [])
        ],
        parts_data=[
            {
                "id": p.id,
                "part_name": p.part_name,
                "part_number": p.part_number,
                "inventory_coverage_days": float(p.inventory_coverage_days)
                if p.inventory_coverage_days is not None
                else None,
                "typical_lead_time_days": float(p.typical_lead_time_days)
                if p.typical_lead_time_days is not None
                else None,
            }
            for p in supplier.parts
        ],
        sources_data=[
            {
                "id": s.id,
                "url_original": s.url_original,
                "url_canonical": s.url_canonical,
                "publisher_name": s.publisher_name,
                "domain": s.domain,
                "published_at": str(s.published_at) if s.published_at else None,
                "retrieved_at": str(s.retrieved_at),
                "content_status": s.content_status,
                "content_hash": s.content_hash,
            }
            for s in sources
        ],
        source_relations_data=[
            {
                "source_a_id": rel.source_a_id,
                "source_b_id": rel.source_b_id,
                "relation": rel.relation,
                "evidence": rel.evidence,
            }
            for rel in source_rels
        ],
        claims_data=[
            {
                "id": c.id,
                "subject_text": c.subject_text,
                "source_id": c.source_id,
                "claim_type": c.claim_type,
                "event_type": c.event_type,
                "supporting_quote": c.supporting_quote,
                "extraction_status": c.extraction_status,
                "polarity": c.polarity,
                "event_date": c.event_date,
            }
            for c in claims
        ],
        incident_data={
            "id": incident.id,
            "event_type": incident.event_type,
            "entity_match_status": incident.entity_match_status,
            "evidence_status": incident.evidence_status,
            "reporting_group_count": incident.reporting_group_count,
            "independent_support_count": incident.independent_support_count,
            "claim_ids": incident.claim_ids,
        }
        if incident
        else None,
        exposure_data={
            "id": incident.exposure.id,
            "potential_inventory_gap_days": float(incident.exposure.potential_inventory_gap_days)
            if incident.exposure.potential_inventory_gap_days is not None
            else None,
            "exposure_band": incident.exposure.exposure_band,
            "calculation_name": incident.exposure.calculation_name,
        }
        if incident and incident.exposure
        else None,
        policy_data={
            "id": incident.policy_decision.id,
            "recommendation": incident.policy_decision.recommendation,
            "rule_ids_fired": incident.policy_decision.rule_ids_fired,
            "reasons": incident.policy_decision.reasons,
        }
        if incident and incident.policy_decision
        else None,
    )
    return graph.to_dict()


@router.get("/investigations/{run_id}/trace")
async def get_investigation_trace(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Retrieve the next-best-investigation execution trace and VOI step history."""
    run = await db.get(InvestigationRunModel, run_id)
    if not run:
        raise NotFoundError(f"Investigation {run_id} not found")

    metrics = run.metrics_json or {}
    trace = metrics.get("investigation_trace")
    if trace:
        return trace

    return {
        "enabled": False,
        "initial_recommendation": None,
        "final_recommendation": None,
        "recommendation_changed": False,
        "identified_gaps": [],
        "steps": [],
    }
