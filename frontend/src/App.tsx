import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getHealth,
  getProvidersHealth,
  listSuppliers,
  createSupplier,
  createInvestigation,
  getInvestigation,
  getInvestigationSources,
  getInvestigationRelations,
  getInvestigationClaims,
  getInvestigationIncidents,
  recordHumanDecision,
  getIncidentReviews,
  listAuditEvents,
  type Supplier,
  type InvestigationRun,
  type IncidentCandidate,
  type HumanReviewAction,
  type PolicyRecommendation,
} from './lib/api'

// ---- Demo Scenarios ----
const DEMO_SCENARIOS = [
  {
    key: 'dresden',
    title: 'Scenario A: Genuine Critical Disruption',
    badge: 'Urgent Review Expected',
    badgeClass: 'pill-danger',
    supplierName: 'Silicon Foundry Dresden GmbH',
    country: 'Germany',
    domain: 'silicon-dresden.de',
    partName: 'Automotive Microcontroller MCU-4',
    coverage: '14',
    recovery: '45',
    criticality: 'high' as const,
    summary:
      'Wafer fab cleanroom fire halting 300mm output for 45 days. Buyer has 14-day stock, resulting in a 31-day operational gap.',
  },
  {
    key: 'titan',
    title: 'Scenario B: True but Irrelevant Incident',
    badge: 'Contingency / Monitor',
    badgeClass: 'pill-warning',
    supplierName: 'Titan Energy Solutions',
    country: 'United States',
    domain: 'titan-energy.com',
    partName: 'Battery Module Pack-B',
    coverage: '30',
    recovery: '10',
    criticality: 'medium' as const,
    summary:
      'Transformer explosion at a regional commercial distribution substation with zero manufacturing plant or assembly impact.',
  },
  {
    key: 'vertex',
    title: 'Scenario C: Similar Name / Misleading Attribution',
    badge: 'Identity Blocker Expected',
    badgeClass: 'pill-neutral',
    supplierName: 'Vertex Components Ltd',
    country: 'United Kingdom',
    domain: 'vertex-components.co.uk',
    partName: 'Industrial Fastener Steel Bolt',
    coverage: '60',
    recovery: null,
    criticality: 'low' as const,
    summary:
      'Cyber incident reported on "Vertex Ltd" based in Melbourne, Australia. Entity resolution flags geographic contradiction/mismatch, blocking false escalation.',
  },
]

export default function App() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'intake' | 'workspace' | 'evidence' | 'decision' | 'audit'>('intake')
  const [searchMode, setSearchMode] = useState<'fixture' | 'live'>('fixture')

  // Selected entities for the active workspace
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null)

  // Human review form state
  const [decisionAction, setDecisionAction] = useState<HumanReviewAction>('approve_recommendation')
  const [overrideRec, setOverrideRec] = useState<PolicyRecommendation | ''>('')
  const [reviewerName, setReviewerName] = useState<string>('Senior Sourcing Specialist')
  const [reviewerNote, setReviewerNote] = useState<string>('')
  const [decisionFeedback, setDecisionFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [investigationError, setInvestigationError] = useState<string | null>(null)

  // Query: System health
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30_000,
  })

  // Query: Providers health
  const { data: providersHealth } = useQuery({
    queryKey: ['providers-health'],
    queryFn: getProvidersHealth,
  })

  // Query: Suppliers
  const { data: suppliersData } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => listSuppliers({ limit: 50 }),
  })

  // Query: Active Investigation Run
  const { data: run, isLoading: isRunLoading } = useQuery({
    queryKey: ['investigation', activeRunId],
    queryFn: () => (activeRunId ? getInvestigation(activeRunId) : null),
    enabled: Boolean(activeRunId),
    refetchInterval: (query) => {
      const data = query.state.data as InvestigationRun | null | undefined
      return data?.status && ['queued', 'searching', 'extracting', 'resolving'].includes(data.status) ? 2000 : false
    },
  })

  // Query: Active Investigation Incidents
  const { data: incidents = [] } = useQuery({
    queryKey: ['investigation-incidents', activeRunId],
    queryFn: () => (activeRunId ? getInvestigationIncidents(activeRunId) : []),
    enabled: Boolean(activeRunId),
  })

  // Active Incident Candidate
  const activeIncident: IncidentCandidate | undefined =
    incidents.find((inc) => inc.id === activeIncidentId) ?? incidents[0]

  // Query: Active Investigation Sources & Relations
  const { data: sources = [] } = useQuery({
    queryKey: ['investigation-sources', activeRunId],
    queryFn: () => (activeRunId ? getInvestigationSources(activeRunId) : []),
    enabled: Boolean(activeRunId),
  })

  const { data: relations = [] } = useQuery({
    queryKey: ['investigation-relations', activeRunId],
    queryFn: () => (activeRunId ? getInvestigationRelations(activeRunId) : []),
    enabled: Boolean(activeRunId),
  })

  // Query: Active Investigation Claims
  const { data: claims = [] } = useQuery({
    queryKey: ['investigation-claims', activeRunId],
    queryFn: () => (activeRunId ? getInvestigationClaims(activeRunId) : []),
    enabled: Boolean(activeRunId),
  })

  // Query: Reviews for Active Incident
  const { data: reviews = [] } = useQuery({
    queryKey: ['incident-reviews', activeIncident?.id],
    queryFn: () => (activeIncident ? getIncidentReviews(activeIncident.id) : []),
    enabled: Boolean(activeIncident?.id),
  })

  // Query: Audit Log
  const { data: auditEvents = [] } = useQuery({
    queryKey: ['audit-events'],
    queryFn: () => listAuditEvents(50),
    enabled: activeTab === 'audit',
  })

  // Mutation: Launch Investigation
  const launchMutation = useMutation({
    mutationFn: async ({ supplierId, mode }: { supplierId: string; mode: 'fixture' | 'live' }) => {
      setInvestigationError(null)
      return createInvestigation({
        supplier_id: supplierId,
        search_mode: mode,
      })
    },
    onSuccess: (res) => {
      setActiveRunId(res.id)
      setActiveIncidentId(null)
      queryClient.invalidateQueries({ queryKey: ['investigation', res.id] })
      setActiveTab('workspace')
    },
    onError: (err: any) => {
      setInvestigationError(err.message || 'Failed to start investigation')
    },
  })

  // Mutation: Record Human Decision
  const reviewMutation = useMutation({
    mutationFn: async () => {
      if (!activeIncident) throw new Error('No incident selected')
      setDecisionFeedback(null)

      const isOverride =
        decisionAction in ['reject_recommendation', 'mark_monitor_only'] ||
        (overrideRec && overrideRec !== activeIncident.policy_decision?.recommendation)

      if (isOverride && (!reviewerNote || reviewerNote.trim().length < 5)) {
        throw new Error('An explicit reviewer rationale (at least 5 characters) is required for overrides.')
      }

      return recordHumanDecision(activeIncident.id, {
        action: decisionAction,
        override_recommendation: overrideRec ? (overrideRec as PolicyRecommendation) : null,
        reviewer_name: reviewerName,
        reviewer_note: reviewerNote,
      })
    },
    onSuccess: () => {
      setDecisionFeedback({
        type: 'success',
        msg: 'Human decision recorded successfully and appended to the immutable audit log.',
      })
      queryClient.invalidateQueries({ queryKey: ['incident-reviews', activeIncident?.id] })
      queryClient.invalidateQueries({ queryKey: ['investigation-incidents', activeRunId] })
      queryClient.invalidateQueries({ queryKey: ['audit-events'] })
    },
    onError: (err: any) => {
      setDecisionFeedback({ type: 'error', msg: err.message || 'Failed to record decision' })
    },
  })

  // Helper: Trigger Scenario
  const handleLaunchScenario = async (sc: (typeof DEMO_SCENARIOS)[0]) => {
    try {
      setInvestigationError(null)
      let supplier = suppliersData?.items.find((s) => s.name === sc.supplierName)
      if (!supplier) {
        supplier = await createSupplier({
          name: sc.supplierName,
          country_or_region: sc.country,
          official_domains: [sc.domain],
          criticality: sc.criticality,
          parts: [
            {
              part_name: sc.partName,
              inventory_coverage_days: sc.coverage,
              recovery_duration_days: sc.recovery,
              criticality: sc.criticality,
            } as any,
          ],
        })
      }
      setSelectedSupplier(supplier as Supplier)
      launchMutation.mutate({ supplierId: supplier.id, mode: searchMode })
    } catch (err: any) {
      setInvestigationError(err.message || 'Scenario initialization failed')
    }
  }

  const isLiveSearchAvailable = Boolean(providersHealth?.search?.configured)

  return (
    <div className="container">
      {/* Header */}
      <header className="app-header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            SupplyChain Sentinel
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Evidence-First Supplier Incident Intelligence & Deterministic Policy Gate
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <span className={`pill ${health?.status === 'ok' ? 'pill-success' : 'pill-danger'}`}>
            <span
              style={{
                display: 'inline-block',
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: health?.status === 'ok' ? 'var(--accent)' : 'var(--error)',
                boxShadow: health?.status === 'ok' ? '0 0 6px var(--accent)' : 'none',
              }}
            />
            API {health?.status === 'ok' ? 'ONLINE' : 'DEGRADED'}
          </span>
          <span className="pill pill-info">
            MODEL: {providersHealth?.llm?.model_id || 'qwen3.5:9b'}
          </span>
          <span className={`pill ${isLiveSearchAvailable ? 'pill-success' : 'pill-neutral'}`}>
            LIVE TAVILY: {isLiveSearchAvailable ? 'READY' : 'NOT CONFIGURED'}
          </span>
        </div>
      </header>

      {/* Global Mode Notice */}
      {searchMode === 'fixture' ? (
        <div className="banner-fixture">
          <div>
            <strong>ACTIVE SEARCH MODE: SIMULATED FIXTURE (Default)</strong> — Retrieved evidence is sourced from
            deterministic fixtures designed for reproducible evaluation.
          </div>
          <span className="pill pill-info">Simulated Evidence</span>
        </div>
      ) : (
        <div className="banner-warning">
          <strong>ACTIVE SEARCH MODE: LIVE TAVILY SEARCH</strong> — Performing live web retrieval. External API
          failures will be reported explicitly without silent fallback.
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className="tabs-container">
        <button
          className={`tab-btn ${activeTab === 'intake' ? 'active' : ''}`}
          onClick={() => setActiveTab('intake')}
        >
          1. Intake & Scenarios
        </button>
        <button
          className={`tab-btn ${activeTab === 'workspace' ? 'active' : ''}`}
          onClick={() => setActiveTab('workspace')}
        >
          2. Investigation Workspace {activeRunId && <span className="pill pill-info">Active</span>}
        </button>
        <button
          className={`tab-btn ${activeTab === 'evidence' ? 'active' : ''}`}
          onClick={() => setActiveTab('evidence')}
        >
          3. Evidence & Quote Inspector ({claims.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'decision' ? 'active' : ''}`}
          onClick={() => setActiveTab('decision')}
        >
          4. Human Decision Gate {activeIncident?.review_required && <span className="pill pill-danger">Review Req.</span>}
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          5. Audit Trail
        </button>
      </nav>

      {/* Global Error Banner */}
      {investigationError && (
        <div className="banner-error" role="alert">
          <strong>Investigation Error:</strong> {investigationError}
          <div style={{ marginTop: '0.4rem' }}>
            {searchMode === 'live' && (
              <button
                className="btn btn-outline"
                style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem' }}
                onClick={() => {
                  setSearchMode('fixture')
                  setInvestigationError(null)
                }}
              >
                Switch to Simulated Fixture Mode & Retry
              </button>
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 1: INTAKE & SCENARIOS                                      */}
      {/* ============================================================== */}
      {activeTab === 'intake' && (
        <div>
          {/* Search Mode Selection Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <span className="card-title">Investigation Search Mode</span>
              <span className="pill pill-neutral">Explicit Control</span>
            </div>
            <div className="card-body" style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="searchMode"
                  value="fixture"
                  checked={searchMode === 'fixture'}
                  onChange={() => setSearchMode('fixture')}
                />
                <div>
                  <strong style={{ color: 'var(--text-primary)' }}>Simulated Fixture Mode (Recommended for Demos)</strong>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Deterministic, reproducible scenarios. Zero network latency or external API keys needed.
                  </div>
                </div>
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.6rem',
                  cursor: isLiveSearchAvailable ? 'pointer' : 'not-allowed',
                  opacity: isLiveSearchAvailable ? 1 : 0.6,
                }}
              >
                <input
                  type="radio"
                  name="searchMode"
                  value="live"
                  checked={searchMode === 'live'}
                  onChange={() => isLiveSearchAvailable && setSearchMode('live')}
                  disabled={!isLiveSearchAvailable}
                />
                <div>
                  <strong style={{ color: 'var(--text-primary)' }}>Live Web Search (Tavily)</strong>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {isLiveSearchAvailable
                      ? 'Queries real web indices. Never silently falls back if an error occurs.'
                      : 'Requires TAVILY_API_KEY in backend .env to enable.'}
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* 1-Click Pre-packaged Demo Scenarios */}
          <div style={{ marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
              Quick-Launch Demonstration Scenarios
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
              Select a scenario to instantly instantiate the supplier profile and execute an investigation.
            </p>

            <div className="grid-3">
              {DEMO_SCENARIOS.map((sc) => (
                <div key={sc.key} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                  <div className="card-header">
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{sc.title}</span>
                    <span className={`pill ${sc.badgeClass}`}>{sc.badge}</span>
                  </div>
                  <div className="card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.85rem', flex: 1 }}>
                      {sc.summary}
                    </p>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                      <div>Supplier: <strong>{sc.supplierName}</strong> ({sc.country})</div>
                      <div>Part: <code>{sc.partName}</code> ({sc.coverage}d stock)</div>
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleLaunchScenario(sc)}
                      disabled={launchMutation.isPending}
                    >
                      {launchMutation.isPending ? 'Investigating…' : 'Launch Scenario'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Supplier Directory Table */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Existing Suppliers Directory</span>
              <span className="pill pill-neutral">{suppliersData?.total || 0} Registered</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Supplier Name</th>
                    <th>Region</th>
                    <th>Criticality</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {suppliersData?.items.map((sup) => (
                    <tr key={sup.id}>
                      <td>
                        <strong style={{ color: 'var(--text-primary)' }}>{sup.name}</strong>
                        {sup.aliases.length > 0 && (
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            Aliases: {sup.aliases.join(', ')}
                          </div>
                        )}
                      </td>
                      <td>{sup.country_or_region || 'Unknown'}</td>
                      <td>
                        <span
                          className={`pill ${
                            sup.criticality === 'high'
                              ? 'pill-danger'
                              : sup.criticality === 'medium'
                              ? 'pill-warning'
                              : 'pill-neutral'
                          }`}
                        >
                          {sup.criticality}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-outline"
                          style={{ padding: '0.3rem 0.7rem', fontSize: '0.82rem' }}
                          onClick={() => {
                            setSelectedSupplier(sup as any)
                            launchMutation.mutate({ supplierId: sup.id, mode: searchMode })
                          }}
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  ))}
                  {(!suppliersData || suppliersData.items.length === 0) && (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                        No suppliers registered yet. Click one of the demo scenarios above to begin.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: INVESTIGATION WORKSPACE                                 */}
      {/* ============================================================== */}
      {activeTab === 'workspace' && (
        <div>
          {!activeRunId ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <h3 style={{ color: 'var(--text-primary)' }}>No Active Investigation</h3>
              <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
                Please select or launch a scenario from the Intake tab.
              </p>
              <button className="btn btn-primary" onClick={() => setActiveTab('intake')}>
                Go to Intake & Scenarios
              </button>
            </div>
          ) : (
            <div>
              {/* Investigation Header */}
              <div className="card">
                <div className="card-header">
                  <div>
                    <span className="card-title">Investigation Run: {run?.id}</span>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      Supplier: <strong style={{ color: 'var(--text-primary)' }}>{selectedSupplier?.name || run?.supplier_id}</strong> | Pipeline v{run?.pipeline_version}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span
                      className={`pill ${
                        run?.status === 'completed'
                          ? 'pill-success'
                          : run?.status === 'failed'
                          ? 'pill-danger'
                          : 'pill-info'
                      }`}
                    >
                      {run?.status.toUpperCase()}
                    </span>
                    {run?.metrics_json?.search_mode === 'fixture' && (
                      <span className="pill pill-neutral">Simulated Evidence</span>
                    )}
                  </div>
                </div>

                <div className="card-body">
                  {isRunLoading && <p style={{ color: 'var(--text-muted)' }}>Executing multi-stage investigation pipeline…</p>}

                  {/* Incident Candidate Findings */}
                  {activeIncident && (
                    <div>
                      <div className="grid-2">
                        {/* 1. Incident & Entity Details */}
                        <div style={{ border: '1px solid var(--border)', background: 'var(--surface-elevated)', borderRadius: 'var(--radius-md)', padding: '1.1rem' }}>
                          <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                            Incident Candidate & Identity
                          </h4>
                          <div style={{ fontSize: '0.88rem', lineHeight: 1.8 }}>
                            <div>
                              <strong style={{ color: 'var(--text-secondary)' }}>Disruption Category:</strong>{' '}
                              <code>{activeIncident.event_type || 'operational_disruption'}</code>
                            </div>
                            <div>
                              <strong style={{ color: 'var(--text-secondary)' }}>Facility / Location:</strong>{' '}
                              <span style={{ color: 'var(--text-primary)' }}>{activeIncident.facility_location || 'Not specified'}</span>
                            </div>
                            <div>
                              <strong style={{ color: 'var(--text-secondary)' }}>Entity Resolution Status (Rules ID-001–005):</strong>{' '}
                              <span
                                className={`pill ${
                                  activeIncident.entity_match_status === 'confirmed'
                                    ? 'pill-success'
                                    : activeIncident.entity_match_status === 'probable'
                                    ? 'pill-info'
                                    : activeIncident.entity_match_status === 'ambiguous'
                                    ? 'pill-warning'
                                    : 'pill-danger'
                                }`}
                              >
                                {activeIncident.entity_match_status}
                              </span>
                            </div>
                            <div>
                              <strong style={{ color: 'var(--text-secondary)' }}>Lineage Corroboration:</strong>{' '}
                              <span style={{ color: 'var(--text-primary)' }}>
                                {activeIncident.independent_support_count !== null
                                  ? `${activeIncident.independent_support_count} independent reporting groups`
                                  : `${sources.length} sources (syndicated wire deduplication active)`}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* 2. Operational Exposure Calculation */}
                        <div style={{ border: '1px solid var(--border)', background: 'var(--surface-elevated)', borderRadius: 'var(--radius-md)', padding: '1.1rem' }}>
                          <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                            Deterministic Exposure (Formula EX-003)
                          </h4>
                          <div style={{ fontSize: '0.88rem', lineHeight: 1.8 }}>
                            <div>
                              <strong style={{ color: 'var(--text-secondary)' }}>Calculation Formula:</strong>{' '}
                              <code>Gap = max(0, Disruption - Coverage)</code>
                            </div>
                            {(() => {
                              const inputVals = activeIncident.exposure?.input_values_json as
                                | Record<string, { value?: unknown }>
                                | undefined
                              const dur = inputVals?.disruption_duration_days?.value
                              const cov = inputVals?.inventory_coverage_days?.value
                              return (
                                <>
                                  <div>
                                    <strong style={{ color: 'var(--text-secondary)' }}>Disruption Duration:</strong>{' '}
                                    <span style={{ color: 'var(--text-primary)' }}>
                                      {dur !== undefined && dur !== null
                                        ? `${String(dur)} days`
                                        : 'UNKNOWN (never assumed zero)'}
                                    </span>
                                  </div>
                                  <div>
                                    <strong style={{ color: 'var(--text-secondary)' }}>Inventory Coverage:</strong>{' '}
                                    <span style={{ color: 'var(--text-primary)' }}>
                                      {cov !== undefined && cov !== null ? `${String(cov)} days` : 'UNKNOWN'}
                                    </span>
                                  </div>
                                </>
                              )
                            })()}
                            <div>
                              <strong style={{ color: 'var(--text-secondary)' }}>Calculated Operational Gap:</strong>{' '}
                              <strong style={{ fontSize: '1.05rem', color: 'var(--error)' }}>
                                {activeIncident.exposure?.potential_inventory_gap_days !== null &&
                                activeIncident.exposure?.potential_inventory_gap_days !== undefined
                                  ? `${activeIncident.exposure.potential_inventory_gap_days} DAYS`
                                  : 'UNKNOWN / NOT CALCULABLE'}
                              </strong>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* 3. Deterministic Policy Recommendation */}
                      <div
                        style={{
                          marginTop: '1.25rem',
                          padding: '1.25rem',
                          background: 'var(--surface-elevated)',
                          border: '1px solid var(--border-strong)',
                          borderRadius: 'var(--radius-md)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              Deterministic Policy Rulebook Evaluation
                            </span>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '0.2rem', color: 'var(--text-primary)' }}>
                              Recommendation:{' '}
                              <span
                                className={`pill ${
                                  activeIncident.policy_decision?.recommendation === 'urgent_human_review'
                                    ? 'pill-danger'
                                    : activeIncident.policy_decision?.recommendation === 'request_supplier_confirmation'
                                    ? 'pill-warning'
                                    : 'pill-info'
                                }`}
                                style={{ fontSize: '0.88rem', padding: '0.3rem 0.8rem' }}
                              >
                                {activeIncident.policy_decision?.recommendation.replace(/_/g, ' ').toUpperCase()}
                              </span>
                            </h3>
                          </div>
                          <div>
                            <button className="btn btn-primary" onClick={() => setActiveTab('decision')}>
                              Open Human Decision Gate
                            </button>
                          </div>
                        </div>

                        {/* Rules fired and blockers */}
                        <div style={{ marginTop: '0.85rem', fontSize: '0.88rem' }}>
                          <div>
                            <strong style={{ color: 'var(--text-secondary)' }}>Rules Fired:</strong>{' '}
                            {activeIncident.policy_decision?.rule_ids_fired.map((r) => (
                              <code key={r} style={{ marginRight: '0.4rem' }}>
                                {r}
                              </code>
                            ))}
                          </div>
                          {activeIncident.policy_decision?.reasons && activeIncident.policy_decision.reasons.length > 0 && (
                            <div style={{ marginTop: '0.4rem' }}>
                              <strong style={{ color: 'var(--text-secondary)' }}>Evaluation Reasons:</strong>
                              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.2rem', color: 'var(--text-secondary)' }}>
                                {activeIncident.policy_decision.reasons.map((rs, i) => (
                                  <li key={i}>{rs}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {activeIncident.policy_decision?.blockers && activeIncident.policy_decision.blockers.length > 0 && (
                            <div style={{ marginTop: '0.4rem', color: 'var(--warning)' }}>
                              <strong>Active Blockers:</strong>
                              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.2rem' }}>
                                {activeIncident.policy_decision.blockers.map((b, i) => (
                                  <li key={i}>{b}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {!activeIncident && !isRunLoading && (
                    <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                      No incident candidates generated for this investigation run.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 3: EVIDENCE & QUOTE INSPECTOR (Constraint 2A)              */}
      {/* ============================================================== */}
      {activeTab === 'evidence' && (
        <div>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Extracted Incident Claims & Verbatim Quote Verification</span>
              <span className="pill pill-neutral">Rule E-005 Verification</span>
            </div>
            <div className="card-body">
              <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                All LLM outputs are treated as untrusted claims until supporting quotes are mathematically verified as
                exact substrings within stored source documents.
              </p>

              {claims.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                  No claims available. Please launch an investigation first.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {claims.map((claim) => {
                    const sourceDoc = sources.find((s) => s.id === claim.source_id)
                    const isVerified = claim.extraction_status === 'validated'

                    return (
                      <div
                        key={claim.id}
                        style={{
                          border: '1px solid var(--border)',
                          borderRadius: 'var(--radius-md)',
                          padding: '1.25rem',
                          background: 'var(--surface-elevated)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div>
                            <span style={{ fontWeight: 700, fontSize: '0.98rem', color: 'var(--text-primary)' }}>
                              {claim.subject_text}
                            </span>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                              <strong>Claimed Disruption:</strong> {claim.object_text}
                            </div>
                          </div>
                          <div>
                            <span className={`pill ${isVerified ? 'pill-success' : 'pill-danger'}`}>
                              {isVerified ? 'VERIFIED QUOTE (Rule E-005)' : 'QUOTE MISMATCH / UNVERIFIED'}
                            </span>
                          </div>
                        </div>

                        {/* Exact Supporting Quotation */}
                        <div style={{ marginTop: '0.75rem' }}>
                          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Literal Supporting Quotation:
                          </span>
                          <div className={`quote-box ${isVerified ? 'quote-verified' : 'quote-mismatch'}`}>
                            "{claim.supporting_quote || 'No quotation extracted'}"
                          </div>
                        </div>

                        {/* Source Document Lineage & Metadata */}
                        {sourceDoc && (
                          <div
                            style={{
                              marginTop: '0.75rem',
                              padding: '0.75rem 1rem',
                              background: 'var(--surface)',
                              border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '0.82rem',
                              color: 'var(--text-secondary)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                              <div>
                                <strong>Publisher:</strong> {sourceDoc.publisher_name || sourceDoc.domain} |{' '}
                                <strong>Published:</strong> {sourceDoc.published_at ? new Date(sourceDoc.published_at).toLocaleDateString() : 'Unknown date'}
                              </div>
                              <div>
                                <a href={sourceDoc.url_original} target="_blank" rel="noopener noreferrer">
                                  Open Source URL ({sourceDoc.domain})
                                </a>
                              </div>
                            </div>
                            {sourceDoc.license_or_usage_notes && (
                              <div style={{ marginTop: '0.3rem', color: 'var(--text-muted)' }}>
                                <em>{sourceDoc.license_or_usage_notes}</em>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Lineage & Duplicate Relations */}
          {relations.length > 0 && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Source Lineage & Syndicated Reporting Analysis</span>
                <span className="pill pill-info">{relations.length} Relations Detected</span>
              </div>
              <div className="card-body">
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Multiple web reports originating from the same wire service (e.g. Reuters) are clustered to prevent
                  false double-counting of corroborating evidence.
                </p>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Source Pair</th>
                      <th>Relation Type</th>
                      <th>Lineage Observation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {relations.map((rel) => (
                      <tr key={rel.id}>
                        <td>
                          <code>{rel.source_a_id.slice(0, 8)}</code> ↔ <code>{rel.source_b_id.slice(0, 8)}</code>
                        </td>
                        <td>
                          <span className="pill pill-warning">{rel.relation}</span>
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>
                          {String(
                            (rel.evidence as Record<string, unknown>)?.observation ||
                              'Content match indicates common origin or wire syndication.'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 4: HUMAN DECISION GATE (Constraint 2B)                     */}
      {/* ============================================================== */}
      {activeTab === 'decision' && (
        <div>
          {!activeIncident ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <h3 style={{ color: 'var(--text-primary)' }}>No Incident Available for Review</h3>
              <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                Please run an investigation to generate a policy recommendation.
              </p>
            </div>
          ) : (
            <div>
              {/* Proposed Action Card */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Human Review Gate: Incident Disposition</span>
                  <span
                    className={`pill ${
                      activeIncident.review_required ? 'pill-danger' : 'pill-success'
                    }`}
                  >
                    {activeIncident.review_required ? 'Review Required' : 'Reviewed & Disposed'}
                  </span>
                </div>
                <div className="card-body">
                  <div
                    style={{
                      padding: '1.1rem',
                      background: 'var(--surface-elevated)',
                      border: '1px solid var(--border-strong)',
                      borderRadius: 'var(--radius-md)',
                      marginBottom: '1.25rem',
                    }}
                  >
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      AUTOMATED POLICY RECOMMENDATION
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.3rem 0' }}>
                      {activeIncident.policy_decision?.recommendation.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                      {activeIncident.policy_decision?.reasons?.join(' ') ||
                        'Evidence and exposure thresholds evaluated deterministically.'}
                    </div>
                  </div>

                  {/* Decision Form */}
                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      reviewMutation.mutate()
                    }}
                  >
                    <div className="form-group">
                      <label className="form-label">Reviewer Action Disposition:</label>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                          <input
                            type="radio"
                            name="decisionAction"
                            value="approve_recommendation"
                            checked={decisionAction === 'approve_recommendation'}
                            onChange={() => setDecisionAction('approve_recommendation')}
                          />
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Accept & Approve Automated Recommendation</strong>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              Accept policy outcome without altering the recommended course of action.
                            </div>
                          </div>
                        </label>

                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                          <input
                            type="radio"
                            name="decisionAction"
                            value="request_more_information"
                            checked={decisionAction === 'request_more_information'}
                            onChange={() => setDecisionAction('request_more_information')}
                          />
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Request Formal Supplier Confirmation</strong>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              Send formal inquiry to supplier account manager before enacting procurement changes.
                            </div>
                          </div>
                        </label>

                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                          <input
                            type="radio"
                            name="decisionAction"
                            value="mark_monitor_only"
                            checked={decisionAction === 'mark_monitor_only'}
                            onChange={() => setDecisionAction('mark_monitor_only')}
                          />
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Mark as Monitor Only</strong>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              De-escalate to ongoing monitoring (e.g. if recovery plan is already confirmed).
                            </div>
                          </div>
                        </label>

                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                          <input
                            type="radio"
                            name="decisionAction"
                            value="reject_recommendation"
                            checked={decisionAction === 'reject_recommendation'}
                            onChange={() => setDecisionAction('reject_recommendation')}
                          />
                          <div>
                            <strong style={{ color: 'var(--text-primary)' }}>Reject / Override Recommendation</strong>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              Requires explicit justification note explaining the human override.
                            </div>
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* Override Recommendation Selection */}
                    {(decisionAction === 'reject_recommendation' || decisionAction === 'mark_monitor_only') && (
                      <div className="form-group" style={{ marginTop: '1rem' }}>
                        <label className="form-label">Explicit Override Recommendation Target:</label>
                        <select
                          className="form-select"
                          value={overrideRec}
                          onChange={(e) => setOverrideRec(e.target.value as PolicyRecommendation)}
                        >
                          <option value="">Select target recommendation…</option>
                          <option value="monitor">Monitor Only</option>
                          <option value="request_supplier_confirmation">Request Supplier Confirmation</option>
                          <option value="review_contingency_plan">Review Contingency Plan</option>
                          <option value="urgent_human_review">Urgent Human Review</option>
                        </select>
                      </div>
                    )}

                    <div className="grid-2">
                      <div className="form-group">
                        <label className="form-label">Reviewer Name / Title:</label>
                        <input
                          type="text"
                          className="form-input"
                          value={reviewerName}
                          onChange={(e) => setReviewerName(e.target.value)}
                          required
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label">
                        Reviewer Rationale & Justification Notes{' '}
                        {decisionAction === 'reject_recommendation' && (
                          <span style={{ color: 'var(--error)' }}>*(Required for Override)*</span>
                        )}
                      </label>
                      <textarea
                        className="form-textarea"
                        rows={3}
                        value={reviewerNote}
                        onChange={(e) => setReviewerNote(e.target.value)}
                        placeholder="Provide the operational justification, direct supplier communications, or context informing this decision…"
                      />
                    </div>

                    {decisionFeedback && (
                      <div
                        className={decisionFeedback.type === 'success' ? 'banner-fixture' : 'banner-error'}
                        style={{ marginBottom: '1rem' }}
                      >
                        {decisionFeedback.msg}
                      </div>
                    )}

                    <button
                      type="submit"
                      className="btn btn-success"
                      disabled={reviewMutation.isPending}
                    >
                      {reviewMutation.isPending ? 'Recording Decision…' : 'Record Human Decision'}
                    </button>
                  </form>
                </div>
              </div>

              {/* Persisted Human Review History */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Recorded Review Decisions History</span>
                  <span className="pill pill-neutral">{reviews.length} Decisions Recorded</span>
                </div>
                <div className="card-body">
                  {reviews.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
                      No prior human reviews recorded for this incident.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {reviews.map((rev) => (
                        <div
                          key={rev.id}
                          style={{
                            padding: '0.85rem 1.1rem',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)',
                            background: 'var(--surface-elevated)',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ color: 'var(--text-primary)' }}>{rev.reviewer_name || 'Procurement Reviewer'}</strong>{' '}
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                on {new Date(rev.reviewed_at).toLocaleString()}
                              </span>
                            </div>
                            <span className="pill pill-success">{rev.action.replace(/_/g, ' ')}</span>
                          </div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
                            <div>
                              Prior automated recommendation:{' '}
                              <code>{rev.prior_recommendation || 'None'}</code>
                              {rev.override_recommendation && (
                                <span> → Overridden to <code>{rev.override_recommendation}</code></span>
                              )}
                            </div>
                            {rev.reviewer_note && (
                              <div style={{ marginTop: '0.3rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                                Note: "{rev.reviewer_note}"
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 5: AUDIT LOG                                               */}
      {/* ============================================================== */}
      {activeTab === 'audit' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Immutable Audit Trail</span>
            <span className="pill pill-neutral">{auditEvents.length} Events Logged</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Entity Type</th>
                  <th>Payload Summary</th>
                </tr>
              </thead>
              <tbody>
                {auditEvents.map((evt) => (
                  <tr key={evt.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      {new Date(evt.created_at).toLocaleString()}
                    </td>
                    <td>
                      <span className="pill pill-info">{evt.event_type}</span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{evt.entity_type || 'system'}</td>
                    <td>
                      <code style={{ fontSize: '0.78rem' }}>
                        {JSON.stringify(evt.data).slice(0, 120)}
                        {JSON.stringify(evt.data).length > 120 ? '…' : ''}
                      </code>
                    </td>
                  </tr>
                ))}
                {auditEvents.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No audit events logged yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
