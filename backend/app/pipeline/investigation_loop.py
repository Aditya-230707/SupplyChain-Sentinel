"""
Bounded Next-Best-Investigation Loop.

The core differentiating capability of SupplyChain Sentinel:
1. Identifies material unresolved evidentiary gaps (missing duration, ambiguous entity,
   single uncorroborated source, conflicting claims, unverified facility).
2. Generates targeted research hypotheses grounded in observed gaps.
3. Ranks candidates using a transparent Heuristic Value of Information (VOI) function.
4. Executes the highest-value search within strict bounds (budget, iteration count, time limit).
5. Re-evaluates claims, exposure, and policy to determine if the recommendation changed.
6. Persists a comprehensive, inspectable investigation trace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass
class EvidenceGap:
    """An identified gap in the current evidence record."""

    gap_type: str
    description: str
    target_entity: str
    impact_weight: float  # 0.0 to 1.0


@dataclass
class CandidateInvestigation:
    """A proposed targeted search action to close an evidence gap."""

    action_id: str
    query: str
    targeted_gap: str
    rationale: str
    expected_source_type: str  # company_statement | regulatory | news_verification
    heuristic_score: float = 0.0
    ranking_details: dict[str, float] = field(default_factory=dict)


@dataclass
class StepTraceRecord:
    """Trace record of one investigation loop iteration."""

    step_number: int
    query: str
    targeted_gap: str
    rationale: str
    heuristic_score: float
    new_sources_count: int
    new_claims_count: int
    prior_recommendation: str
    new_recommendation: str
    recommendation_changed: bool
    termination_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "query": self.query,
            "targeted_gap": self.targeted_gap,
            "rationale": self.rationale,
            "heuristic_score": self.heuristic_score,
            "new_sources_count": self.new_sources_count,
            "new_claims_count": self.new_claims_count,
            "prior_recommendation": self.prior_recommendation,
            "new_recommendation": self.new_recommendation,
            "recommendation_changed": self.recommendation_changed,
            "termination_reason": self.termination_reason,
        }


def identify_evidence_gaps(
    supplier_name: str,
    entity_status: str,
    evidence_status: str,
    reporting_group_count: int,
    has_duration: bool,
    has_contradictions: bool,
    facility_matched: bool,
) -> list[EvidenceGap]:
    """Identify material unresolved evidence gaps that impair decision confidence."""
    gaps: list[EvidenceGap] = []

    # Gap 1: Ambiguous or mismatched corporate entity
    if entity_status in ("ambiguous", "mismatch", "unknown"):
        gaps.append(
            EvidenceGap(
                gap_type="ambiguous_identity",
                description=f"Corporate entity match for '{supplier_name}' is '{entity_status}'.",
                target_entity=supplier_name,
                impact_weight=0.95,
            )
        )

    # Gap 2: Disputed / contradictory reports
    if has_contradictions:
        gaps.append(
            EvidenceGap(
                gap_type="conflicting_claims",
                description="Contradictory claims detected (e.g. disruption vs drill/exercise).",
                target_entity=supplier_name,
                impact_weight=0.90,
            )
        )

    # Gap 3: Missing recovery duration
    if not has_duration:
        gaps.append(
            EvidenceGap(
                gap_type="missing_duration",
                description="No quantitative recovery duration or restart timeline found.",
                target_entity=supplier_name,
                impact_weight=0.80,
            )
        )

    # Gap 4: Single uncorroborated source
    if reporting_group_count <= 1 and evidence_status != "outdated_or_resolved":
        gaps.append(
            EvidenceGap(
                gap_type="single_unverified_source",
                description="Incident reported by single source group without corroboration.",
                target_entity=supplier_name,
                impact_weight=0.75,
            )
        )

    # Gap 5: Facility unresolved
    if not facility_matched:
        gaps.append(
            EvidenceGap(
                gap_type="facility_unresolved",
                description="Specific facility affected is not verified against buyer plants.",
                target_entity=supplier_name,
                impact_weight=0.60,
            )
        )

    return gaps


def generate_candidate_investigations(
    supplier_name: str,
    gaps: list[EvidenceGap],
    executed_queries: list[str],
) -> list[CandidateInvestigation]:
    """Generate grounded search candidates to resolve each identified evidence gap."""
    candidates: list[CandidateInvestigation] = []
    executed_lower = {q.lower().strip() for q in executed_queries}
    clean_supplier = supplier_name.replace('"', "").strip()

    for idx, gap in enumerate(gaps):
        cand: CandidateInvestigation | None = None

        if gap.gap_type == "missing_duration":
            cand = CandidateInvestigation(
                action_id=f"act_dur_{idx}",
                query=f'"{clean_supplier}" restart timeline recovery weeks duration operational',
                targeted_gap=gap.gap_type,
                rationale="Search for estimated facility repair duration or restart timeline.",
                expected_source_type="company_statement",
            )
        elif gap.gap_type == "conflicting_claims":
            cand = CandidateInvestigation(
                action_id=f"act_conf_{idx}",
                query=(
                    f'"{clean_supplier}" drill exercise correction false alarm official statement'
                ),
                targeted_gap=gap.gap_type,
                rationale="Search for corporate clarification or resolution notice.",
                expected_source_type="regulatory",
            )
        elif gap.gap_type == "single_unverified_source":
            cand = CandidateInvestigation(
                action_id=f"act_corrob_{idx}",
                query=f'"{clean_supplier}" press release official statement incident disruption',
                targeted_gap=gap.gap_type,
                rationale="Seek independent primary confirmation to corroborate press report.",
                expected_source_type="company_statement",
            )
        elif gap.gap_type == "ambiguous_identity":
            cand = CandidateInvestigation(
                action_id=f"act_ident_{idx}",
                query=f'"{clean_supplier}" headquarters stock ticker corporate registry',
                targeted_gap=gap.gap_type,
                rationale="Disambiguate corporate legal entity, jurisdiction, and ticker.",
                expected_source_type="regulatory",
            )
        elif gap.gap_type == "facility_unresolved":
            cand = CandidateInvestigation(
                action_id=f"act_fac_{idx}",
                query=f'"{clean_supplier}" manufacturing plant fab location facility damage fire',
                targeted_gap=gap.gap_type,
                rationale="Pinpoint exact manufacturing plant or cleanroom building affected.",
                expected_source_type="news_verification",
            )

        if cand and cand.query.lower().strip() not in executed_lower:
            candidates.append(cand)

    return candidates


def rank_investigation_candidates(
    candidates: list[CandidateInvestigation],
    gaps: list[EvidenceGap],
    executed_queries: list[str],
) -> list[CandidateInvestigation]:
    """Score and rank candidate actions using transparent Heuristic Value of Information (VOI).

    Formula:
    VOI(q) = (Relevance * 0.35) + (Impact * 0.35) + (Quality * 0.20) - (Redundancy * 0.10)
    """
    gap_impact_map = {g.gap_type: g.impact_weight for g in gaps}
    executed_words = {w for q in executed_queries for w in q.lower().split()}

    for cand in candidates:
        impact = gap_impact_map.get(cand.targeted_gap, 0.5)
        relevance = (
            0.90 if cand.targeted_gap in ("missing_duration", "conflicting_claims") else 0.75
        )
        quality = 0.90 if cand.expected_source_type == "company_statement" else 0.70

        # Redundancy penalty based on word overlap with previous queries
        q_words = set(cand.query.lower().split())
        overlap = len(q_words & executed_words) / max(1, len(q_words))
        redundancy_penalty = round(overlap * 0.5, 2)

        score = round(
            (relevance * 0.35) + (impact * 0.35) + (quality * 0.20) - (redundancy_penalty * 0.10),
            3,
        )

        cand.heuristic_score = score
        cand.ranking_details = {
            "relevance_weight": relevance,
            "unresolved_impact_weight": impact,
            "expected_source_quality": quality,
            "redundancy_penalty": redundancy_penalty,
            "total_heuristic_voi": score,
        }

    # Sort descending by heuristic score
    candidates.sort(key=lambda c: c.heuristic_score, reverse=True)
    return candidates
