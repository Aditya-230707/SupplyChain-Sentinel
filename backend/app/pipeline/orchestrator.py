"""
Investigation orchestrator — executes one complete end-to-end investigation slice.

Coordinates:
1. Search & retrieve raw metadata
2. URL canonicalization & source deduplication (E-001, E-002)
3. Content extraction & snippet labelling (E-004)
4. Source lineage & reporting group clustering (E-003, EV-001, EV-002)
5. Structured claim extraction via LLM
6. Quote verification against stored text (E-005)
7. Multi-signal supplier entity resolution (ID-001 to ID-005)
8. Deterministic exposure assessment (EX-001 to EX-006)
9. Deterministic policy evaluation (P-001 to P-010)
10. Database persistence of all artifacts and audit events
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.db.models import (
    AuditEvent as AuditEventModel,
)
from app.db.models import (
    Claim as ClaimModel,
)
from app.db.models import (
    ClaimRelation as ClaimRelationModel,
)
from app.db.models import (
    ExposureAssessment as ExposureAssessmentModel,
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
    SourceRelation as SourceRelationModel,
)
from app.db.models import (
    Supplier as SupplierModel,
)
from app.pipeline.claim_validator import verify_quote_against_source
from app.pipeline.entity_resolution import (
    SupplierProfile,
    resolve_supplier_entity,
)
from app.pipeline.evidence_graph import (
    FacilityProfile,
    build_investigation_evidence_graph,
    detect_claim_semantic_relations,
    resolve_facility_entity,
)
from app.pipeline.exposure_calculator import (
    PartExposureInput,
    calculate_operational_exposure,
)
from app.pipeline.policy_engine import (
    IncidentEvidenceSnapshot,
    evaluate_policy_rules,
)
from app.pipeline.source_lineage import (
    SourceCandidate,
    analyze_source_lineage,
)
from app.pipeline.source_normalizer import canonicalize_url, compute_content_hash
from app.providers.content_base import ContentProvider
from app.providers.llm_base import LLMProvider
from app.providers.search_base import SearchProvider
from app.schemas.claim import ClaimExtractionResponse

log = structlog.get_logger(__name__)


def _load_extraction_prompt() -> str:
    from pathlib import Path

    prompt_file = Path(__file__).resolve().parent.parent / "prompts" / "claim_extraction_v1.txt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return "Extract discrete factual claims from the source text relevant to supplier incidents."


async def run_investigation(
    investigation_id: str,
    db: AsyncSession,
    *,
    search_provider: SearchProvider,
    content_provider: ContentProvider,
    llm_provider: LLMProvider,
) -> InvestigationRunModel:
    """Execute the end-to-end investigation pipeline."""
    start_time = time.perf_counter()
    run = await db.get(InvestigationRunModel, investigation_id)
    if not run:
        raise NotFoundError(f"Investigation {investigation_id} not found")

    # Load supplier with parts and facilities
    stmt = (
        select(SupplierModel)
        .options(
            selectinload(SupplierModel.parts),
            selectinload(SupplierModel.facilities),
        )
        .where(SupplierModel.id == run.supplier_id)
    )
    supplier = (await db.execute(stmt)).scalar_one_or_none()
    if not supplier:
        run.status = "failed"
        run.error_code = "supplier_not_found"
        run.error_summary = f"Supplier {run.supplier_id} not found"
        await db.flush()
        return run

    profile = SupplierProfile(
        id=supplier.id,
        name=supplier.name,
        aliases=supplier.aliases,
        official_domains=supplier.official_domains,
        registry_ids=supplier.registry_ids,
        country_or_region=supplier.country_or_region,
        parts=[p.part_name for p in supplier.parts],
    )

    facilities_profile = [
        FacilityProfile(
            id=f.id,
            name=f.facility_name,
            facility_type=f.facility_type,
            country_or_region=f.country_or_region,
            city_or_address=f.city_or_address,
            criticality=f.criticality,
        )
        for f in (supplier.facilities or [])
    ]

    run.status = "searching"
    run.started_at = datetime.now(UTC).replace(tzinfo=None)
    run.provider_name = llm_provider.provider_name
    run.model_name = llm_provider.model_id
    await db.flush()

    warnings: list[str] = []

    # Stage 1: Bounded Search Queries
    query = f'"{supplier.name}" incident OR disruption OR factory OR shutdown'
    search_resp = await search_provider.search(query, max_results=6)
    if search_resp.status in ("provider_error", "quota_exceeded"):
        warnings.append(
            f"Search provider warning: {search_resp.status} ({search_resp.error_message})"
        )

    # Stage 2: Deduplicate & Normalize URLs
    raw_results = search_resp.results
    candidates_by_canonical: dict[str, Any] = {}
    for r in raw_results:
        canon = canonicalize_url(r.url)
        if canon not in candidates_by_canonical:
            candidates_by_canonical[canon] = r

    # Stage 3: Retrieve Content
    urls_to_extract = [r.url for r in candidates_by_canonical.values()]
    content_results = await content_provider.extract(urls_to_extract)
    content_by_url = {c.url: c for c in content_results}

    # Build SourceCandidate objects
    source_candidates: list[SourceCandidate] = []
    source_db_records: dict[str, SourceDocumentModel] = {}

    for canon, r in candidates_by_canonical.items():
        extracted = content_by_url.get(r.url)
        content_text = (
            extracted.text if extracted and extracted.status == "available" else r.snippet
        )
        content_status = (
            "available" if (extracted and extracted.status == "available") else "snippet_only"
        )
        chash = compute_content_hash(content_text)

        s_cand = SourceCandidate(
            id=f"src_{len(source_candidates) + 1}",
            url_original=r.url,
            url_canonical=canon,
            title=r.title,
            domain=r.domain,
            publisher_name=r.domain,
            content_text=content_text,
            content_hash=chash,
            content_status=content_status,
        )
        source_candidates.append(s_cand)

        # Create DB record
        src_model = SourceDocumentModel(
            investigation_id=run.id,
            url_original=r.url,
            url_canonical=canon,
            title=r.title,
            domain=r.domain,
            publisher_name=r.domain,
            content_excerpt=content_text[:2000] if content_text else None,
            content_hash=chash,
            content_status=content_status,
            source_class="established_media" if "news" in (r.domain or "") else "unknown",
        )
        db.add(src_model)
        source_db_records[s_cand.id] = src_model

    await db.flush()

    # Stage 4: Analyze Lineage
    lineage = analyze_source_lineage(source_candidates)
    for rel in lineage.relations:
        src_a = source_db_records.get(rel.source_a_id)
        src_b = source_db_records.get(rel.source_b_id)
        if src_a and src_b:
            rel_model = SourceRelationModel(
                source_a_id=src_a.id,
                source_b_id=src_b.id,
                relation=rel.relation,
                evidence=rel.evidence,
                review_status=rel.review_status,
            )
            db.add(rel_model)

    await db.flush()

    # Stage 5: Structured Claim Extraction
    run.status = "extracting"
    await db.flush()
    extraction_prompt = _load_extraction_prompt()

    extracted_claims_list: list[dict[str, Any]] = []

    for s_cand in source_candidates:
        if not s_cand.content_text:
            continue

        src_model = source_db_records[s_cand.id]
        payload = {
            "source_id": src_model.id,
            "title": s_cand.title,
            "source_text": s_cand.content_text[:8000],  # Bounded input
            "supplier_context": {"name": supplier.name, "aliases": supplier.aliases},
        }

        try:
            model_res = await llm_provider.generate_structured(
                task_name="claim_extraction",
                system_prompt=extraction_prompt,
                user_payload=payload,
                response_model=ClaimExtractionResponse,
            )
            parsed: ClaimExtractionResponse = model_res.parsed_output  # type: ignore[assignment]
            for claim_item in parsed.claims:
                # Stage 6: Quote verification
                q_val = verify_quote_against_source(
                    claim_item.supporting_quote, s_cand.content_text
                )

                # Stage 7: Entity Resolution
                ent_res = resolve_supplier_entity(
                    supplier=profile,
                    subject_text=claim_item.subject_text,
                    source_text=s_cand.content_text,
                    source_domain=s_cand.domain,
                    location_text=claim_item.location_text,
                )

                # Facility Resolution
                fac_res = resolve_facility_entity(
                    claim_item.location_text,
                    claim_item.subject_text,
                    facilities_profile,
                )

                claim_model = ClaimModel(
                    investigation_id=run.id,
                    source_id=src_model.id,
                    subject_text=claim_item.subject_text,
                    subject_candidate_supplier_id=supplier.id
                    if ent_res.status in ("confirmed", "probable")
                    else None,
                    event_type=claim_item.event_type,
                    object_text=claim_item.object_text,
                    event_date=claim_item.event_date,
                    event_date_precision=claim_item.event_date_precision,
                    location_text=claim_item.location_text,
                    claim_type=claim_item.claim_type,
                    polarity=claim_item.polarity,
                    supporting_quote=claim_item.supporting_quote,
                    quote_start=q_val.quote_start,
                    quote_end=q_val.quote_end,
                    extraction_status=q_val.status,
                    evidence_limitations=claim_item.evidence_limitations,
                )
                db.add(claim_model)
                extracted_claims_list.append(
                    {
                        "claim_model": claim_model,
                        "entity_res": ent_res,
                        "facility_res": fac_res,
                        "quote_val": q_val,
                    }
                )
        except Exception as exc:
            warnings.append(f"Extraction failed on source {s_cand.url_canonical}: {str(exc)[:100]}")

    await db.flush()

    # Stage 7b: Semantic Claim Relationships (Corroboration, Contradiction, Echo)
    source_to_group: dict[str, str] = {}
    for rel in lineage.relations:
        if rel.relation in ("syndicated", "near_duplicate", "exact_duplicate"):
            source_to_group[rel.source_b_id] = rel.source_a_id

    claim_dicts_for_rel = [
        {
            "id": c["claim_model"].id,
            "claim_type": c["claim_model"].claim_type,
            "event_type": c["claim_model"].event_type,
            "source_id": c["claim_model"].source_id,
            "polarity": c["claim_model"].polarity,
        }
        for c in extracted_claims_list
    ]
    claim_semantic_rels = detect_claim_semantic_relations(claim_dicts_for_rel, source_to_group)
    for cr in claim_semantic_rels:
        cr_model = ClaimRelationModel(
            claim_a_id=cr.claim_a_id,
            claim_b_id=cr.claim_b_id,
            relation=cr.relation,
            rationale=cr.rationale,
            detected_rule=cr.rule_id,
        )
        db.add(cr_model)
    await db.flush()

    has_contradictions = any(cr.relation == "contradicts" for cr in claim_semantic_rels)

    # Stage 8: Incident Candidate Synthesis
    run.status = "resolving"
    await db.flush()

    # Determine primary incident candidate if claims exist
    incident_model: IncidentCandidateModel | None = None
    exposure_model: ExposureAssessmentModel | None = None
    policy_model: PolicyDecisionModel | None = None

    if extracted_claims_list:
        # Determine aggregate entity match status
        statuses = [c["entity_res"].status for c in extracted_claims_list]
        overall_entity_status = "unknown"
        if "confirmed" in statuses:
            overall_entity_status = "confirmed"
        elif "probable" in statuses:
            overall_entity_status = "probable"
        elif "ambiguous" in statuses:
            overall_entity_status = "ambiguous"
        elif "mismatch" in statuses:
            overall_entity_status = "mismatch"

        # Evidence status
        ev_status = "single_source" if lineage.reporting_group_count <= 1 else "corroborated"
        has_resolutions = any(
            c["claim_model"].claim_type in ("resolution", "correction")
            for c in extracted_claims_list
        )
        if has_resolutions:
            ev_status = "outdated_or_resolved"

        # Matched facility if any
        matched_fac_id = None
        matched_fac_name = None
        for c in extracted_claims_list:
            fac = c["facility_res"]
            if fac.status in ("confirmed", "probable") and fac.matched_facility:
                matched_fac_id = fac.matched_facility.id
                matched_fac_name = fac.matched_facility.name
                break

        first_claim = extracted_claims_list[0]["claim_model"]
        search_mode = run.metrics_json.get("search_mode", "fixture")
        contra_count = sum(1 for cr in claim_semantic_rels if cr.relation == "contradicts")
        incident_model = IncidentCandidateModel(
            investigation_id=run.id,
            supplier_id=supplier.id if overall_entity_status in ("confirmed", "probable") else None,
            facility_id=matched_fac_id,
            search_mode=search_mode,
            event_type=first_claim.event_type or "operational_disruption",
            facility_location=matched_fac_name or first_claim.location_text,
            event_date_start=first_claim.event_date,
            claim_ids=[c["claim_model"].id for c in extracted_claims_list],
            entity_match_status=overall_entity_status,
            evidence_status=ev_status,
            reporting_group_count=lineage.reporting_group_count,
            independent_support_count=lineage.independent_support_count,
            contradiction_summary=(
                f"{contra_count} contradictory claim relationships detected."
                if has_contradictions
                else None
            ),
            review_required=True,
        )
        db.add(incident_model)
        await db.flush()

        # Stage 9: Deterministic Exposure Calculation
        run.status = "assessing_impact"
        await db.flush()

        part_input: PartExposureInput | None = None
        if supplier.parts:
            primary_part = supplier.parts[0]
            part_input = PartExposureInput(
                part_name=primary_part.part_name,
                inventory_coverage_days=primary_part.inventory_coverage_days,
                typical_lead_time_days=primary_part.typical_lead_time_days,
                recovery_duration_days=primary_part.recovery_duration_days,
                alternative_available=primary_part.alternative_supplier_available,
                criticality=supplier.criticality,
            )

        exposure_res = calculate_operational_exposure(part_input)
        exposure_inputs_rich = {
            **exposure_res.input_values,
            "scenarios": exposure_res.scenarios,
            "expected_decision_losses": exposure_res.expected_decision_losses,
            "sensitivity_analysis": exposure_res.sensitivity_analysis,
            "gap_min_days": float(exposure_res.potential_inventory_gap_min_days)
            if exposure_res.potential_inventory_gap_min_days is not None
            else None,
            "gap_max_days": float(exposure_res.potential_inventory_gap_max_days)
            if exposure_res.potential_inventory_gap_max_days is not None
            else None,
        }
        exposure_model = ExposureAssessmentModel(
            incident_id=incident_model.id,
            input_values_json=exposure_inputs_rich,
            calculation_name=exposure_res.calculation_name,
            calculation_version=exposure_res.calculation_version,
            potential_inventory_gap_days=exposure_res.potential_inventory_gap_days,
            criticality=exposure_res.criticality,
            alternative_available=exposure_res.alternative_available,
            exposure_band=exposure_res.exposure_band,
            assumptions=exposure_res.assumptions,
            limitations=exposure_res.limitations,
        )
        db.add(exposure_model)

        # Stage 10: Deterministic Policy Evaluation
        run.status = "adjudicating"
        await db.flush()

        # Build snapshot
        snapshot = IncidentEvidenceSnapshot(
            entity_match_status=overall_entity_status,
            evidence_status=ev_status,
            event_type=incident_model.event_type,
            reporting_group_count=lineage.reporting_group_count,
            has_contradictions=has_contradictions,
            has_resolution_or_correction=has_resolutions,
            provider_failed=len(warnings) > 0 and not extracted_claims_list,
        )

        policy_res = evaluate_policy_rules(
            evidence=snapshot,
            exposure=exposure_res,
            entity=extracted_claims_list[0]["entity_res"],
        )

        policy_model = PolicyDecisionModel(
            incident_id=incident_model.id,
            policy_version=policy_res.policy_version,
            recommendation=policy_res.recommendation,
            rule_ids_fired=policy_res.rule_ids_fired,
            input_snapshot=policy_res.input_snapshot,
            reasons=policy_res.reasons,
            blockers=policy_res.blockers,
            human_review_required=policy_res.human_review_required,
        )
        db.add(policy_model)

    # Build Evidence DAG and Provenance Metrics
    evidence_graph = build_investigation_evidence_graph(
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
            for s in source_db_records.values()
        ],
        source_relations_data=[
            {
                "source_a_id": rel.source_a_id,
                "source_b_id": rel.source_b_id,
                "relation": rel.relation,
                "evidence": rel.evidence,
            }
            for rel in lineage.relations
        ],
        claims_data=[
            {
                "id": c["claim_model"].id,
                "subject_text": c["claim_model"].subject_text,
                "source_id": c["claim_model"].source_id,
                "claim_type": c["claim_model"].claim_type,
                "event_type": c["claim_model"].event_type,
                "supporting_quote": c["claim_model"].supporting_quote,
                "extraction_status": c["claim_model"].extraction_status,
                "polarity": c["claim_model"].polarity,
                "event_date": c["claim_model"].event_date,
            }
            for c in extracted_claims_list
        ],
        incident_data={
            "id": incident_model.id,
            "event_type": incident_model.event_type,
            "entity_match_status": incident_model.entity_match_status,
            "evidence_status": incident_model.evidence_status,
            "reporting_group_count": incident_model.reporting_group_count,
            "independent_support_count": incident_model.independent_support_count,
            "claim_ids": incident_model.claim_ids,
        }
        if incident_model
        else None,
        exposure_data={
            "id": exposure_model.id,
            "potential_inventory_gap_days": float(exposure_model.potential_inventory_gap_days)
            if exposure_model and exposure_model.potential_inventory_gap_days is not None
            else None,
            "exposure_band": exposure_model.exposure_band if exposure_model else "unknown",
            "calculation_name": exposure_model.calculation_name if exposure_model else "none",
        }
        if exposure_model
        else None,
        policy_data={
            "id": policy_model.id,
            "recommendation": policy_model.recommendation,
            "rule_ids_fired": policy_model.rule_ids_fired,
            "reasons": policy_model.reasons,
        }
        if policy_model
        else None,
    )

    run.metrics_json = {
        **run.metrics_json,
        "provenance": evidence_graph.metrics,
    }

    # Append Audit Event
    audit_event = AuditEventModel(
        event_type="investigation_run",
        entity_type="investigation_runs",
        entity_id=run.id,
        data={
            "supplier_id": supplier.id,
            "sources_count": len(source_candidates),
            "claims_count": len(extracted_claims_list),
            "warnings_count": len(warnings),
            "provenance_score": evidence_graph.metrics.get("data_completeness_score"),
        },
    )
    db.add(audit_event)

    # Stage 11: Complete investigation
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    run.completed_at = datetime.now(UTC).replace(tzinfo=None)
    run.status = "completed_with_warnings" if warnings else "completed"
    run.metrics_json = {
        "elapsed_ms": round(elapsed_ms, 1),
        "source_count": lineage.source_count,
        "reporting_group_count": lineage.reporting_group_count,
        "claims_extracted": len(extracted_claims_list),
        "warnings": warnings,
    }

    await db.flush()
    await db.refresh(run)
    return run
