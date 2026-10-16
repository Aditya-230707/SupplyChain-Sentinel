/**
 * Domain types for SupplyChain Sentinel frontend.
 *
 * These mirror Pydantic backend schemas.
 * Labels distinguish: fact | inference | assumption | recommendation
 */

// Re-export from api.ts for components that need only types
export type {
  AppHealth,
  Supplier,
  SupplierListItem,
  SupplierListResponse,
  SupplierPart,
  SupplierCreatePayload,
} from '../lib/api'

/** Evidence status — must match backend IncidentCandidate.evidence_status */
export type EvidenceStatus =
  | 'primary_source_reported'
  | 'corroborated'
  | 'single_source'
  | 'disputed'
  | 'unverified'
  | 'outdated_or_resolved'
  | 'false_entity_match'
  | 'unknown'

/** Entity match status */
export type EntityMatchStatus =
  | 'confirmed'
  | 'probable'
  | 'ambiguous'
  | 'mismatch'
  | 'unknown'

/** Policy recommendation — no autonomous high-impact actions */
export type PolicyRecommendation =
  | 'monitor'
  | 'request_supplier_confirmation'
  | 'review_contingency_plan'
  | 'urgent_human_review'
  | 'insufficient_evidence'

/** Human review action — "approve" means acknowledge, not suspend a supplier */
export type HumanReviewAction =
  | 'approve_recommendation'
  | 'reject_recommendation'
  | 'request_more_information'
  | 'mark_monitor_only'

export type InvestigationStatus =
  | 'queued'
  | 'searching'
  | 'extracting'
  | 'resolving'
  | 'adjudicating'
  | 'assessing_impact'
  | 'composing'
  | 'completed'
  | 'completed_with_warnings'
  | 'failed'

/** Source class — transparent category, not a globally correct trust score */
export type SourceClass =
  | 'official_primary'
  | 'company_statement'
  | 'established_media'
  | 'specialist_media'
  | 'other'
  | 'unknown'
