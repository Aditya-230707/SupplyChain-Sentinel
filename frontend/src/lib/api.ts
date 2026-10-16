/**
 * Typed API client for SupplyChain Sentinel backend.
 *
 * All requests go through /api (proxied to FastAPI during dev).
 * Response types mirror the Pydantic schemas on the backend.
 * Never construct URLs with raw user input without encoding.
 */

const BASE = '/api/v1'

class ApiError extends Error {
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

// ---- Health -------------------------------------------------

export interface AppHealth {
  status: 'ok' | 'degraded' | 'error'
  version: string
  environment: string
  timestamp: string
  database: { ok: boolean; error?: string | null }
}

export async function getHealth(): Promise<AppHealth> {
  return request<AppHealth>('GET', '/health')
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
  inventory_coverage_days: string | null  // Decimal as string
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

export async function updateSupplier(id: string, payload: Partial<SupplierCreatePayload>): Promise<Supplier> {
  return request<Supplier>('PATCH', `/suppliers/${encodeURIComponent(id)}`, payload)
}

export { ApiError }
