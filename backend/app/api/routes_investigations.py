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
    if search_mode == "live":
        settings = get_settings()
        if not settings.tavily_api_key:
            raise ProviderUnavailableError(
                "TAVILY_API_KEY is not configured for live search mode. "
                "Set TAVILY_API_KEY in your environment or choose Fixture Search mode."
            )
        search, content = make_tavily_providers_from_settings()
    else:
        # Fixture mode (default): rich demo scenarios tailored to supplier name
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
