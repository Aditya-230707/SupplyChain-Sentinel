"""
End-to-end vertical slice integration tests.

Tests the full pipeline from supplier creation through search, lineage,
claim extraction, quote validation, entity resolution, exposure calculation,
deterministic policy evaluation, and database persistence.

Scenarios tested:
1. Genuine, relevant supplier incident (confirmed entity + positive gap).
2. True but irrelevant incident (mismatched entity -> no action).
3. Similar-name / ambiguous attribution (blocks urgent recommendation).
4. Duplicate / syndicated wire-service reporting (counted once for corroboration).
5. Corrected / resolved incident (P-007 monitor).
6. Missing inventory/recovery inputs (gap remains null, P-004).
7. Malformed LLM output & provider error resilience (completed_with_warnings).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
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
    PolicyDecision as PolicyDecisionModel,
)
from app.db.models import (
    SourceDocument as SourceDocumentModel,
)
from app.db.models import (
    Supplier as SupplierModel,
)
from app.db.models import (
    SupplierPart as SupplierPartModel,
)
from app.pipeline.orchestrator import run_investigation
from app.providers.fake_provider import FakeLLMProvider
from app.providers.fixture_search_provider import (
    FixtureContentProvider,
    FixtureSearchProvider,
)
from app.providers.search_base import SearchResult
from app.schemas.claim import ClaimExtractionResponse, ExtractedClaimItem


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Isolated in-memory SQLite database session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


# ---- 1. Genuine, relevant supplier incident -----------------


@pytest.mark.asyncio
async def test_genuine_relevant_incident_workflow(db_session: AsyncSession) -> None:
    # Setup supplier
    supplier = SupplierModel(
        name="Silicon Foundry Dresden GmbH",
        official_domains=["silicon-dresden.de"],
        country_or_region="Germany",
        criticality="high",
    )
    db_session.add(supplier)
    await db_session.flush()

    part = SupplierPartModel(
        supplier_id=supplier.id,
        part_name="Automotive Power IC",
        inventory_coverage_days=Decimal("15"),
        typical_lead_time_days=Decimal("30"),
        recovery_duration_days=Decimal("45"),
        relationship_source="source_evidence",
    )
    db_session.add(part)

    run = InvestigationRunModel(
        supplier_id=supplier.id,
        status="queued",
        requested_categories=["operational_disruption"],
    )
    db_session.add(run)
    await db_session.flush()

    # Fixture source
    article_text = (
        "Silicon Foundry Dresden GmbH experienced a severe cleanroom fire on Tuesday. "
        "Company officials confirmed the plant will halt wafer output for approximately 45 days. "
        "Firefighters from Saxony responded to the emergency at the Dresden industrial park."
    )
    search_provider = FixtureSearchProvider(
        [
            SearchResult(
                url="https://press.silicon-dresden.de/news/cleanroom-incident?utm_source=rss",
                title="Fire incident at Dresden fab",
                snippet="Silicon Foundry Dresden GmbH confirms cleanroom fire.",
                domain="press.silicon-dresden.de",
                published_date="2026-10-10",
                provider_score=0.95,
            )
        ],
    )
    content_provider = FixtureContentProvider(
        {
            "https://press.silicon-dresden.de/news/cleanroom-incident?utm_source=rss": article_text,
        }
    )

    # Fake LLM extraction with exact quote
    llm_output = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="Silicon Foundry Dresden GmbH",
                event_type="operational_disruption",
                object_text="Severe cleanroom fire halting wafer output for approximately 45 days",
                event_date="2026-10-10",
                event_date_precision="day",
                location_text="Dresden, Germany",
                claim_type="incident",
                polarity="supports",
                supporting_quote=(
                    "Silicon Foundry Dresden GmbH experienced a severe cleanroom fire on Tuesday."
                ),
                evidence_limitations=[],
            )
        ]
    )
    llm_provider = FakeLLMProvider(responses=[llm_output])

    # Run pipeline
    completed_run = await run_investigation(
        investigation_id=run.id,
        db=db_session,
        search_provider=search_provider,
        content_provider=content_provider,
        llm_provider=llm_provider,
    )

    assert completed_run.status == "completed"
    assert search_provider.call_count == 4

    assert search_provider.queries[:3] == [
        f'"{supplier.name}"',
        f'"{supplier.name}" incident OR disruption',
        f'"{supplier.name}" factory OR production OR shutdown',
    ]

    # The investigation loop may issue an additional corroboration query.
    assert len(search_provider.queries) == 4
    assert "single_unverified_source" in str(
        completed_run.metrics_json.get("investigation_trace", {})
    )

    # Verify sources stored with canonical URL (stripped UTM)
    sources = (
        (
            await db_session.execute(
                select(SourceDocumentModel).where(SourceDocumentModel.investigation_id == run.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(sources) == 1
    assert "utm_source" not in sources[0].url_canonical

    # Verify claim stored and quote validated
    claims = (
        (await db_session.execute(select(ClaimModel).where(ClaimModel.investigation_id == run.id)))
        .scalars()
        .all()
    )
    assert len(claims) == 1
    assert claims[0].extraction_status == "validated"
    assert claims[0].quote_start is not None

    # Verify incident candidate and deterministic policy recommendation
    incidents = (
        (
            await db_session.execute(
                select(IncidentCandidateModel).where(
                    IncidentCandidateModel.investigation_id == run.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(incidents) == 1
    assert incidents[0].entity_match_status == "confirmed"

    policy_dec = (
        await db_session.execute(
            select(PolicyDecisionModel).where(PolicyDecisionModel.incident_id == incidents[0].id)
        )
    ).scalar_one()

    # Gap = 45 - 15 = 30 days gap -> high exposure on high criticality -> urgent_human_review
    assert policy_dec.recommendation == "urgent_human_review"
    assert "P-005" in policy_dec.rule_ids_fired


# ---- 2. True but irrelevant incident (Entity Mismatch) ------


@pytest.mark.asyncio
async def test_irrelevant_incident_mismatch(db_session: AsyncSession) -> None:
    supplier = SupplierModel(
        name="Atlas Precision Gears Inc",
        country_or_region="United States",
    )
    db_session.add(supplier)
    await db_session.flush()

    run = InvestigationRunModel(supplier_id=supplier.id, status="queued")
    db_session.add(run)
    await db_session.flush()

    article_text = (
        "Titan Energy Solutions reported a transformer explosion at its Houston substation. "
        "No other industrial facilities were affected."
    )
    search_provider = FixtureSearchProvider(
        [
            SearchResult(
                url="https://houstonnews.com/titan-explosion",
                title="Titan Energy Houston explosion",
                snippet="Explosion reported at Titan Energy substation.",
                domain="houstonnews.com",
                published_date="2026-10-12",
                provider_score=0.4,
            )
        ]
    )
    content_provider = FixtureContentProvider(
        {
            "https://houstonnews.com/titan-explosion": article_text,
        }
    )

    llm_output = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="Titan Energy Solutions",
                event_type="operational_disruption",
                object_text="Transformer explosion at Houston substation",
                claim_type="incident",
                polarity="supports",
                supporting_quote=(
                    "Titan Energy Solutions reported a transformer explosion at its "
                    "Houston substation."
                ),
            )
        ]
    )
    llm_provider = FakeLLMProvider(responses=[llm_output])

    completed_run = await run_investigation(
        investigation_id=run.id,
        db=db_session,
        search_provider=search_provider,
        content_provider=content_provider,
        llm_provider=llm_provider,
    )
    assert completed_run.status == "completed"
    incidents = (
        (
            await db_session.execute(
                select(IncidentCandidateModel).where(
                    IncidentCandidateModel.investigation_id == run.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(incidents) == 1
    # Mismatched company -> entity_match_status is mismatch
    assert incidents[0].entity_match_status == "mismatch"

    policy_dec = (
        await db_session.execute(
            select(PolicyDecisionModel).where(PolicyDecisionModel.incident_id == incidents[0].id)
        )
    ).scalar_one()
    # P-001 fires for mismatch -> insufficient_evidence, no action against supplier
    assert policy_dec.recommendation == "insufficient_evidence"
    assert "P-001" in policy_dec.rule_ids_fired


# ---- 3. Similar-name / Ambiguous identity blocks action -----


@pytest.mark.asyncio
async def test_ambiguous_name_blocks_urgent_recommendation(db_session: AsyncSession) -> None:
    # Common single-word company name without domain/registry confirmation
    supplier = SupplierModel(
        name="Vertex Ltd",
        country_or_region="United Kingdom",
        criticality="high",
    )
    db_session.add(supplier)
    await db_session.flush()

    run = InvestigationRunModel(supplier_id=supplier.id, status="queued")
    db_session.add(run)
    await db_session.flush()

    article_text = (
        "Vertex Ltd announced an immediate suspension of assembly lines "
        "following a cyber incident. "
        "The company is based in Melbourne, Australia."  # Country contradicts target UK
    )
    search_provider = FixtureSearchProvider(
        [
            SearchResult(
                url="https://aussie-business.com/vertex-cyber",
                title="Vertex Ltd halts assembly",
                snippet="Vertex Ltd halts assembly lines in Melbourne.",
                domain="aussie-business.com",
                published_date="2026-10-14",
                provider_score=0.8,
            )
        ]
    )
    content_provider = FixtureContentProvider(
        {
            "https://aussie-business.com/vertex-cyber": article_text,
        }
    )

    llm_output = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="Vertex Ltd",
                event_type="operational_disruption",
                object_text="Suspension of assembly lines following cyber incident",
                location_text="Melbourne, Australia",
                claim_type="incident",
                polarity="supports",
                supporting_quote=(
                    "Vertex Ltd announced an immediate suspension of assembly lines "
                    "following a cyber incident."
                ),
            )
        ]
    )
    llm_provider = FakeLLMProvider(responses=[llm_output])

    await run_investigation(
        investigation_id=run.id,
        db=db_session,
        search_provider=search_provider,
        content_provider=content_provider,
        llm_provider=llm_provider,
    )

    incidents = (
        (
            await db_session.execute(
                select(IncidentCandidateModel).where(
                    IncidentCandidateModel.investigation_id == run.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert incidents[0].entity_match_status == "ambiguous"

    policy_dec = (
        await db_session.execute(
            select(PolicyDecisionModel).where(PolicyDecisionModel.incident_id == incidents[0].id)
        )
    ).scalar_one()

    # Rule P-001 must block urgent action and mandate request_supplier_confirmation
    assert policy_dec.recommendation == "request_supplier_confirmation"
    assert "P-001" in policy_dec.rule_ids_fired
    assert policy_dec.human_review_required is True


# ---- 4. Duplicate / Syndicated Wire Reporting ---------------


@pytest.mark.asyncio
async def test_syndicated_reuters_sources_not_double_counted(db_session: AsyncSession) -> None:
    supplier = SupplierModel(
        name="Global Logistics Hub Corp",
        official_domains=["globallogistics.com"],
    )
    db_session.add(supplier)
    await db_session.flush()

    run = InvestigationRunModel(supplier_id=supplier.id, status="queued")
    db_session.add(run)
    await db_session.flush()

    wire_text_1 = (
        "Reuters reports that "
        "Global Logistics Hub Corp port terminal has been closed due to crane collapse."
    )
    wire_text_2 = (
        "According to Reuters, "
        "Global Logistics Hub Corp port terminal is closed after a crane collapse."
    )

    search_provider = FixtureSearchProvider(
        [
            SearchResult(
                url="https://site1.com/story-1",
                title="Port closed",
                snippet="Terminal closed",
                domain="site1.com",
                published_date="2026-10-15",
                provider_score=0.9,
            ),
            SearchResult(
                url="https://site2.com/story-2",
                title="Port closed",
                snippet="Terminal closed",
                domain="site2.com",
                published_date="2026-10-15",
                provider_score=0.9,
            ),
        ]
    )
    content_provider = FixtureContentProvider(
        {
            "https://site1.com/story-1": wire_text_1,
            "https://site2.com/story-2": wire_text_2,
        }
    )

    llm_output = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="Global Logistics Hub Corp",
                event_type="logistics_disruption",
                object_text="Port terminal closed due to crane collapse",
                claim_type="incident",
                polarity="supports",
                supporting_quote=(
                    "Global Logistics Hub Corp port terminal has been closed due to crane collapse."
                ),
            )
        ]
    )
    llm_provider = FakeLLMProvider(responses=[llm_output, llm_output])

    await run_investigation(
        investigation_id=run.id,
        db=db_session,
        search_provider=search_provider,
        content_provider=content_provider,
        llm_provider=llm_provider,
    )

    incidents = (
        (
            await db_session.execute(
                select(IncidentCandidateModel).where(
                    IncidentCandidateModel.investigation_id == run.id
                )
            )
        )
        .scalars()
        .all()
    )

    # Even though 2 URLs were returned, they share Reuters origin -> 1 reporting group
    assert incidents[0].reporting_group_count == 1
    # EV-001 single-source rule fires, NOT corroborated
    assert incidents[0].evidence_status == "single_source"


# ---- 5. Missing inventory / recovery data --------------------


@pytest.mark.asyncio
async def test_missing_inventory_gap_remains_null(db_session: AsyncSession) -> None:
    supplier = SupplierModel(
        name="Pinnacle Fasteners Ltd",
        official_domains=["pinnacle-fasteners.co.uk"],
    )
    db_session.add(supplier)
    await db_session.flush()

    # Part exists, but coverage is unknown (None)
    part = SupplierPartModel(
        supplier_id=supplier.id,
        part_name="Titanium Bolt Set",
        inventory_coverage_days=None,  # unknown
    )
    db_session.add(part)

    run = InvestigationRunModel(supplier_id=supplier.id, status="queued")
    db_session.add(run)
    await db_session.flush()

    text = "Pinnacle Fasteners Ltd experienced an inspection halt at plant 4."
    search_provider = FixtureSearchProvider(
        [
            SearchResult(
                url="https://press.pinnacle-fasteners.co.uk/halt",
                title="Inspection halt",
                snippet="Inspection halt at plant 4.",
                domain="press.pinnacle-fasteners.co.uk",
                published_date="2026-10-15",
                provider_score=0.9,
            )
        ]
    )
    content_provider = FixtureContentProvider(
        {
            "https://press.pinnacle-fasteners.co.uk/halt": text,
        }
    )

    llm_output = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="Pinnacle Fasteners Ltd",
                event_type="operational_disruption",
                object_text="Inspection halt at plant 4",
                claim_type="incident",
                polarity="supports",
                supporting_quote=(
                    "Pinnacle Fasteners Ltd experienced an inspection halt at plant 4."
                ),
            )
        ]
    )
    llm_provider = FakeLLMProvider(responses=[llm_output])

    await run_investigation(
        investigation_id=run.id,
        db=db_session,
        search_provider=search_provider,
        content_provider=content_provider,
        llm_provider=llm_provider,
    )

    incidents = (
        (
            await db_session.execute(
                select(IncidentCandidateModel).where(
                    IncidentCandidateModel.investigation_id == run.id
                )
            )
        )
        .scalars()
        .all()
    )

    # EX-002: Gap must remain null, never zero
    assert incidents[0].exposure.potential_inventory_gap_days is None
    # P-004: Credible event but exposure unknown -> request_supplier_confirmation
    assert incidents[0].policy_decision.recommendation == "request_supplier_confirmation"
    assert "P-004" in incidents[0].policy_decision.rule_ids_fired


# ---- 6. Fabricated quote detection in end-to-end flow --------


@pytest.mark.asyncio
async def test_fabricated_quote_marked_quote_mismatch(db_session: AsyncSession) -> None:
    supplier = SupplierModel(name="SafeTech Sensors Inc")
    db_session.add(supplier)
    await db_session.flush()

    run = InvestigationRunModel(supplier_id=supplier.id, status="queued")
    db_session.add(run)
    await db_session.flush()

    text = "SafeTech Sensors Inc passed the annual ISO audit with flying colors."
    search_provider = FixtureSearchProvider(
        [
            SearchResult(
                url="https://news.safetech.com/audit",
                title="Audit result",
                snippet="Audit passed",
                domain="news.safetech.com",
                published_date="2026-10-15",
                provider_score=0.8,
            )
        ]
    )
    content_provider = FixtureContentProvider({"https://news.safetech.com/audit": text})

    # Model hallucinates a quote that is NOT in the source text
    hallucinated_claim = ClaimExtractionResponse(
        claims=[
            ExtractedClaimItem(
                subject_text="SafeTech Sensors Inc",
                event_type="operational_disruption",
                object_text="Factory closed permanently due to fraud",
                claim_type="incident",
                polarity="supports",
                supporting_quote="The company was forced to shut all operations forever.",
            )
        ]
    )
    llm_provider = FakeLLMProvider(responses=[hallucinated_claim])

    await run_investigation(
        investigation_id=run.id,
        db=db_session,
        search_provider=search_provider,
        content_provider=content_provider,
        llm_provider=llm_provider,
    )

    claims = (
        (await db_session.execute(select(ClaimModel).where(ClaimModel.investigation_id == run.id)))
        .scalars()
        .all()
    )
    assert len(claims) == 1
    # Rule E-005 blocks hallucinated quote
    assert claims[0].extraction_status == "quote_mismatch"
    assert claims[0].quote_start is None
