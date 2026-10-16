/**
 * Typed API client for SupplyChain Sentinel backend.
 *
 * All requests go through /api/v1.
 * Response types mirror the Pydantic schemas on the backend.
 * Never construct URLs with raw user input without encoding.
 */

const BASE = '/api/v1'

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number,
    public readonly requestId?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  const requestId = res.headers.get('X-Request-ID') ?? undefined

  if (!res.ok) {
    let code = 'unknown_error'
    let message = `HTTP ${res.status}`
    try {
      const err = (await res.json()) as { error?: { code?: string; message?: string } }
      code = err.error?.code ?? code
      message = err.error?.message ?? message
    } catch {
      // ignore parse errors
    }
    throw new ApiError(code, message, res.status, requestId)
  }

  return res.json() as Promise<T>
}

// ---- Health & Providers -------------------------------------

export interface AppHealth {
  status: 'ok' | 'degraded' | 'error'
  version: string
  environment: string
  timestamp: string
  database: { ok: boolean; error?: string | null }
}

export interface ProviderHealth {
  provider_name: string
  model_id?: string | null
  configured: boolean
  reachable?: boolean | null
  model_available?: boolean | null
  error?: string | null
}

export interface ProvidersHealthResponse {
  llm: ProviderHealth
  search?: ProviderHealth | null
}

export async function getHealth(): Promise<AppHealth> {
  return request<AppHealth>('GET', '/health')
}

export async function getProvidersHealth(): Promise<ProvidersHealthResponse> {
  return request<ProvidersHealthResponse>('GET', '/health/providers')
}

// ---- Suppliers ----------------------------------------------

export interface SupplierListItem {
  id: string
  name: string
  aliases: string[]
  criticality: 'low' | 'medium' | 'high' | 'unknown'
  active: boolean
  country_or_region: string | null
  created_at: string
  updated_at: string
}

export interface SupplierListResponse {
  items: SupplierListItem[]
  total: number
  limit: number
  offset: number
}

export interface SupplierPart {
  id: string
  supplier_id: string
  part_name: string
  part_number: string | null
  inventory_coverage_days: string | null // Decimal as string
  typical_lead_time_days: string | null
  recovery_duration_days: string | null
  alternative_supplier_available: 'yes' | 'no' | 'unknown'
  business_unit: string | null
  relationship_source: 'user_input' | 'imported_file' | 'source_evidence'
  last_verified_at: string | null
  created_at: string
  updated_at: string
}

export interface Supplier {
  id: string
  name: string
  aliases: string[]
  official_domains: string[]
  registry_ids: string[]
  country_or_region: string | null
  notes: string | null
  criticality: 'low' | 'medium' | 'high' | 'unknown'
  active: boolean
  parts: SupplierPart[]
  created_at: string
  updated_at: string
}

export interface SupplierCreatePayload {
  name: string
  aliases?: string[]
  official_domains?: string[]
  registry_ids?: string[]
  country_or_region?: string | null
  notes?: string | null
  criticality?: 'low' | 'medium' | 'high' | 'unknown'
  active?: boolean
  parts?: Partial<SupplierPart>[]
}

export async function listSuppliers(
  params: { query?: string; limit?: number; offset?: number } = {},
): Promise<SupplierListResponse> {
  const q = new URLSearchParams()
  if (params.query) q.set('query', params.query)
  if (params.limit !== undefined) q.set('limit', String(params.limit))
  if (params.offset !== undefined) q.set('offset', String(params.offset))
  const qs = q.toString() ? `?${q.toString()}` : ''
  return request<SupplierListResponse>('GET', `/suppliers${qs}`)
}

export async function getSupplier(id: string): Promise<Supplier> {
  return request<Supplier>('GET', `/suppliers/${encodeURIComponent(id)}`)
}

export async function createSupplier(payload: SupplierCreatePayload): Promise<Supplier> {
  return request<Supplier>('POST', '/suppliers', payload)
}

// ---- Investigations & Evidence -----------------------------

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

export interface InvestigationRun {
  id: string
  supplier_id: string
  status: InvestigationStatus
  requested_categories: string[]
  started_at?: string | null
  completed_at?: string | null
  pipeline_version: string
  provider_name?: string | null
  model_name?: string | null
  error_code?: string | null
  error_summary?: string | null
  metrics_json: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface InvestigationCreatePayload {
  supplier_id: string
  requested_categories?: string[]
  search_mode?: 'fixture' | 'live'
  date_range_start?: string | null
  date_range_end?: string | null
}

export interface InvestigationCreateResponse {
  id: string
  supplier_id: string
  status: InvestigationStatus
  created_at: string
}

export async function createInvestigation(
  payload: InvestigationCreatePayload,
): Promise<InvestigationCreateResponse> {
  return request<InvestigationCreateResponse>('POST', '/investigations', payload)
}

export async function listInvestigations(limit: number = 20): Promise<InvestigationRun[]> {
  return request<InvestigationRun[]>('GET', `/investigations?limit=${limit}`)
}

export async function getInvestigation(id: string): Promise<InvestigationRun> {
  return request<InvestigationRun>('GET', `/investigations/${encodeURIComponent(id)}`)
}

export interface SourceDocument {
  id: string
  investigation_id: string
  url_original: string
  url_canonical: string
  title?: string | null
  publisher_name?: string | null
  domain?: string | null
  published_at?: string | null
  event_date_candidates: Array<{
    date_text: string
    date_iso?: string | null
    precision: string
    provenance: string
  }>
  content_excerpt?: string | null
  content_hash?: string | null
  provider_result_id?: string | null
  source_class: string
  content_status: 'available' | 'snippet_only' | 'inaccessible' | 'extraction_failed'
  license_or_usage_notes?: string | null
  retrieved_at: string
  created_at: string
}

export async function getInvestigationSources(runId: string): Promise<SourceDocument[]> {
  return request<SourceDocument[]>('GET', `/investigations/${encodeURIComponent(runId)}/sources`)
}

export interface SourceRelation {
  id: string
  source_a_id: string
  source_b_id: string
  relation:
    | 'same_url'
    | 'exact_duplicate'
    | 'near_duplicate'
    | 'syndicated'
    | 'cites_same_origin'
    | 'possible_derivative'
    | 'unknown'
  evidence: Record<string, unknown>
  review_status: 'automatic_candidate' | 'human_confirmed' | 'human_rejected'
  created_at: string
}

export async function getInvestigationRelations(runId: string): Promise<SourceRelation[]> {
  return request<SourceRelation[]>('GET', `/investigations/${encodeURIComponent(runId)}/relations`)
}

export interface Claim {
  id: string
  investigation_id: string
  source_id: string
  subject_text: string
  subject_candidate_supplier_id?: string | null
  event_type?: string | null
  object_text?: string | null
  event_date?: string | null
  event_date_precision: 'day' | 'month' | 'year' | 'unknown'
  location_text?: string | null
  claim_type:
    | 'incident'
    | 'impact'
    | 'response'
    | 'allegation'
    | 'official_finding'
    | 'resolution'
    | 'correction'
    | 'other'
  polarity: 'supports' | 'contradicts' | 'contextual' | 'unknown'
  supporting_quote?: string | null
  quote_start?: number | null
  quote_end?: number | null
  extraction_status: 'validated' | 'quote_mismatch' | 'schema_invalid' | 'needs_review'
  evidence_limitations: string[]
  created_at: string
  updated_at: string
}

export async function getInvestigationClaims(runId: string): Promise<Claim[]> {
  return request<Claim[]>('GET', `/investigations/${encodeURIComponent(runId)}/claims`)
}

// ---- Incidents, Exposure & Policy Decisions ------------------

export type EntityMatchStatus = 'confirmed' | 'probable' | 'ambiguous' | 'mismatch' | 'unknown'

export type EvidenceStatus =
  | 'primary_source_reported'
  | 'corroborated'
  | 'single_source'
  | 'disputed'
  | 'unverified'
  | 'outdated_or_resolved'
  | 'false_entity_match'
  | 'unknown'

export type PolicyRecommendation =
  | 'monitor'
  | 'request_supplier_confirmation'
  | 'review_contingency_plan'
  | 'urgent_human_review'
  | 'insufficient_evidence'

export interface ExposureAssessment {
  id: string
  incident_id: string
  input_values_json: Record<string, unknown>
  calculation_name: string
  calculation_version: string
  potential_inventory_gap_days?: string | null
  criticality: 'low' | 'medium' | 'high' | 'unknown'
  alternative_available: 'yes' | 'no' | 'unknown'
  exposure_band: 'low' | 'moderate' | 'high' | 'unknown'
  assumptions: string[]
  limitations: string[]
  created_at: string
}

export interface PolicyDecision {
  id: string
  incident_id: string
  policy_version: string
  recommendation: PolicyRecommendation
  rule_ids_fired: string[]
  input_snapshot: Record<string, unknown>
  reasons: string[]
  blockers: string[]
  human_review_required: boolean
  created_at: string
}

export interface IncidentCandidate {
  id: string
  investigation_id: string
  supplier_id?: string | null
  event_type?: string | null
  facility_location?: string | null
  event_date_start?: string | null
  event_date_end?: string | null
  claim_ids: string[]
  entity_match_status: EntityMatchStatus
  evidence_status: EvidenceStatus
  reporting_group_count?: number | null
  independent_support_count?: number | null
  contradiction_summary?: string | null
  review_required: boolean
  exposure?: ExposureAssessment | null
  policy_decision?: PolicyDecision | null
  created_at: string
  updated_at: string
}

export async function listIncidents(limit: number = 20): Promise<IncidentCandidate[]> {
  return request<IncidentCandidate[]>('GET', `/incidents?limit=${limit}`)
}

export async function getInvestigationIncidents(runId: string): Promise<IncidentCandidate[]> {
  return request<IncidentCandidate[]>('GET', `/investigations/${encodeURIComponent(runId)}/incidents`)
}

export async function getIncident(incidentId: string): Promise<IncidentCandidate> {
  return request<IncidentCandidate>('GET', `/incidents/${encodeURIComponent(incidentId)}`)
}

// ---- Human Reviews & Audits ---------------------------------

export type HumanReviewAction =
  | 'approve_recommendation'
  | 'reject_recommendation'
  | 'request_more_information'
  | 'mark_monitor_only'

export interface HumanReviewPayload {
  action: HumanReviewAction
  override_recommendation?: PolicyRecommendation | null
  reviewer_name?: string
  reviewer_note?: string | null
}

export interface HumanReview {
  id: string
  policy_decision_id: string
  action: HumanReviewAction
  override_recommendation?: string | null
  reviewer_name?: string | null
  reviewer_note?: string | null
  reviewed_at: string
  prior_recommendation?: string | null
  created_at: string
}

export interface AuditEvent {
  id: string
  event_type: string
  entity_type?: string | null
  entity_id?: string | null
  data: Record<string, unknown>
  created_at: string
}

export async function recordHumanDecision(
  incidentId: string,
  payload: HumanReviewPayload,
): Promise<HumanReview> {
  return request<HumanReview>(
    'POST',
    `/incidents/${encodeURIComponent(incidentId)}/decision`,
    payload,
  )
}

export async function getIncidentReviews(incidentId: string): Promise<HumanReview[]> {
  return request<HumanReview[]>('GET', `/incidents/${encodeURIComponent(incidentId)}/reviews`)
}

export async function listAuditEvents(limit: number = 50): Promise<AuditEvent[]> {
  return request<AuditEvent[]>('GET', `/audit-events?limit=${limit}`)
}
