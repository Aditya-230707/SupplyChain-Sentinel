import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getHealth,
  getProvidersHealth,
  listSuppliers,
  createSupplier,
  createInvestigation,
  listInvestigations,
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

// Benchmark scenarios preserved for deterministic offline verification and testing
const BENCHMARK_SCENARIOS = [
  {
    key: 'dresden',
    title: 'Benchmark A: Genuine Disruption',
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
    title: 'Benchmark B: True Non-Impacting Incident',
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
      'Transformer explosion at regional distribution substation with zero manufacturing plant or assembly impact.',
  },
  {
    key: 'vertex',
    title: 'Benchmark C: Name / Entity Mismatch',
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
      'Cyber incident reported on "Vertex Ltd" based in Melbourne, Australia. Entity resolution flags geographic contradiction, blocking false escalation.',
  },
]

type ActiveTab =
  | 'investigations'
  | 'new_investigation'
  | 'workspace'
  | 'suppliers'
  | 'evidence'
  | 'decision'
  | 'audit'
  | 'telemetry'

export default function App() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<ActiveTab>('investigations')
  const [searchMode, setSearchMode] = useState<'ddg' | 'live' | 'fixture'>('ddg')
  const [showBenchmarkDrawer, setShowBenchmarkDrawer] = useState(false)

  // Selected entities for active investigation workspace
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null)

  // Intake Form Custom Inputs
  const [formSupplierMode, setFormSupplierMode] = useState<'existing' | 'new'>('new')
  const [formExistingSupplierId, setFormExistingSupplierId] = useState<string>('')
  const [formName, setFormName] = useState<string>('')
  const [formCountry, setFormCountry] = useState<string>('')
  const [formDomain, setFormDomain] = useState<string>('')
  const [formCriticality, setFormCriticality] = useState<'low' | 'medium' | 'high' | 'unknown'>('high')
  const [formPartName, setFormPartName] = useState<string>('')
  const [formCoverageDays, setFormCoverageDays] = useState<string>('')
  const [formRecoveryDays, setFormRecoveryDays] = useState<string>('')
  const [formCategories, setFormCategories] = useState<string[]>([
    'operational_disruption',
    'environmental_regulatory',
    'logistics_disruption',
  ])

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
    refetchInterval: 30_000,
  })

  // Query: Suppliers
  const { data: suppliersData } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => listSuppliers({ limit: 50 }),
  })

  // Query: Investigation Runs List
  const { data: investigationsList = [], isLoading: isListLoading } = useQuery({
    queryKey: ['investigations-list'],
    queryFn: () => listInvestigations(50),
    refetchInterval: 4000,
  })

  // Query: Active Investigation Run
  const { data: run, isLoading: isRunLoading } = useQuery({
    queryKey: ['investigation', activeRunId],
    queryFn: () => (activeRunId ? getInvestigation(activeRunId) : null),
    enabled: Boolean(activeRunId),
    refetchInterval: (query) => {
      const data = query.state.data as InvestigationRun | null | undefined
      return data?.status && ['queued', 'searching', 'extracting', 'resolving', 'adjudicating', 'assessing_impact'].includes(data.status)
        ? 1500
        : false
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
    mutationFn: async ({ supplierId, mode, categories }: { supplierId: string; mode: 'fixture' | 'live' | 'ddg'; categories?: string[] }) => {
      setInvestigationError(null)
      return createInvestigation({
        supplier_id: supplierId,
        search_mode: mode,
        requested_categories: categories,
      })
    },
    onSuccess: (res) => {
      setActiveRunId(res.id)
      setActiveIncidentId(null)
      queryClient.invalidateQueries({ queryKey: ['investigation', res.id] })
      queryClient.invalidateQueries({ queryKey: ['investigations-list'] })
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

  // Helper: Trigger Custom Live Investigation from Form
  const handleStartCustomInvestigation = async (e: React.FormEvent) => {
    e.preventDefault()
    setInvestigationError(null)

    try {
      let targetSupplierId = formExistingSupplierId

      if (formSupplierMode === 'new') {
        if (!formName.trim()) {
          setInvestigationError('Supplier name is required.')
          return
        }
        const created = await createSupplier({
          name: formName.trim(),
          country_or_region: formCountry.trim() || null,
          official_domains: formDomain.trim() ? [formDomain.trim()] : [],
          criticality: formCriticality,
          parts: formPartName.trim()
            ? [
                {
                  part_name: formPartName.trim(),
                  inventory_coverage_days: formCoverageDays.trim() || null,
                  recovery_duration_days: formRecoveryDays.trim() || null,
                } as any,
              ]
            : [],
        })
        targetSupplierId = created.id
        setSelectedSupplier(created)
        queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      } else {
        const sup = suppliersData?.items.find((s) => s.id === targetSupplierId)
        if (sup) setSelectedSupplier(sup as any)
      }

      launchMutation.mutate({
        supplierId: targetSupplierId,
        mode: searchMode,
        categories: formCategories,
      })
    } catch (err: any) {
      setInvestigationError(err.message || 'Failed to initiate investigation')
    }
  }

  // Helper: Trigger Benchmark Scenario
  const handleLaunchBenchmarkScenario = async (sc: (typeof BENCHMARK_SCENARIOS)[0]) => {
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
      // Benchmark scenarios use fixture mode to verify policy logic deterministically
      launchMutation.mutate({ supplierId: supplier.id, mode: 'fixture' })
    } catch (err: any) {
      setInvestigationError(err.message || 'Benchmark scenario initialization failed')
    }
  }

  // Navigation Helper
  const navigateToRun = (runItem: InvestigationRun) => {
    setActiveRunId(runItem.id)
    setActiveIncidentId(null)
    const sup = suppliersData?.items.find((s) => s.id === runItem.supplier_id)
    if (sup) setSelectedSupplier(sup as any)
    setActiveTab('workspace')
  }

  const isTavilyAvailable = providersHealth?.search?.provider_name === 'tavily_search'

  return (
    <div className="app-shell">
      {/* ============================================================ */}
      {/* PERSISTENT LEFT NAVIGATION SIDEBAR                           */}
      {/* ============================================================ */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand-sys">Core // Node 01</div>
          <div className="sidebar-brand-title">SENTINEL</div>
          <div className="sidebar-brand-subtitle">Industrial Intelligence</div>
        </div>

        <div className="sidebar-content">
          <div>
            <div className="sidebar-section-title">Navigation</div>
            <div className="sidebar-nav-list">
              <button
                className={`sidebar-nav-item ${activeTab === 'investigations' ? 'active' : ''}`}
                onClick={() => setActiveTab('investigations')}
              >
                <span>Investigations</span>
                <span className="nav-count">{investigationsList.length}</span>
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'new_investigation' ? 'active' : ''}`}
                onClick={() => setActiveTab('new_investigation')}
              >
                <span>+ New Investigation</span>
                <span className="nav-count" style={{ color: 'var(--accent)' }}>LIVE</span>
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'workspace' ? 'active' : ''}`}
                onClick={() => setActiveTab('workspace')}
              >
                <span>Active Workspace</span>
                {activeRunId && <span className="nav-count" style={{ color: 'var(--accent)' }}>{activeRunId.slice(0, 6)}</span>}
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'suppliers' ? 'active' : ''}`}
                onClick={() => setActiveTab('suppliers')}
              >
                <span>Supplier Registry</span>
                <span className="nav-count">{suppliersData?.total || 0}</span>
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'evidence' ? 'active' : ''}`}
                onClick={() => setActiveTab('evidence')}
              >
                <span>Evidence & Quotes</span>
                <span className="nav-count">{claims.length}</span>
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'decision' ? 'active' : ''}`}
                onClick={() => setActiveTab('decision')}
              >
                <span>Human Decision Gate</span>
                {activeIncident?.review_required && (
                  <span className="nav-count" style={{ background: 'rgba(255, 90, 90, 0.2)', color: 'var(--error)' }}>
                    REQ
                  </span>
                )}
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'audit' ? 'active' : ''}`}
                onClick={() => setActiveTab('audit')}
              >
                <span>Audit Ledger</span>
                <span className="nav-count">{auditEvents.length}</span>
              </button>

              <button
                className={`sidebar-nav-item ${activeTab === 'telemetry' ? 'active' : ''}`}
                onClick={() => setActiveTab('telemetry')}
              >
                <span>System Telemetry</span>
                <span className="nav-count">DIAG</span>
              </button>
            </div>
          </div>

          {/* Benchmark Scenarios (Simulated Fixtures) Drawer */}
          <div>
            <div
              className="sidebar-section-title"
              style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer', alignItems: 'center' }}
              onClick={() => setShowBenchmarkDrawer(!showBenchmarkDrawer)}
            >
              <span>Benchmark Suites</span>
              <span style={{ fontSize: '0.7rem' }}>{showBenchmarkDrawer ? '▲' : '▼'}</span>
            </div>

            {showBenchmarkDrawer && (
              <div className="sidebar-benchmarks-box">
                <div className="benchmark-tag">Simulated Fixtures</div>
                <div className="benchmark-desc">
                  Deterministic synthetic scenarios for policy regression tests and offline validation.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {BENCHMARK_SCENARIOS.map((sc) => (
                    <button
                      key={sc.key}
                      className="btn btn-outline"
                      style={{
                        padding: '0.4rem 0.6rem',
                        fontSize: '0.74rem',
                        textAlign: 'left',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.15rem',
                      }}
                      onClick={() => handleLaunchBenchmarkScenario(sc)}
                      disabled={launchMutation.isPending}
                    >
                      <strong style={{ color: 'var(--text-primary)' }}>{sc.title}</strong>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>{sc.supplierName}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Status Footer */}
        <div className="sidebar-footer">
          <div className="engine-status-row">
            <span>LLM ENGINE</span>
            <span className="engine-status-val online">
              {providersHealth?.llm?.model_id || 'qwen3.5:9b'}
            </span>
          </div>
          <div className="engine-status-row">
            <span>WEB SEARCH</span>
            <span className="engine-status-val online">
              {providersHealth?.search?.provider_name === 'tavily_search' ? 'TAVILY' : 'DUCKDUCKGO'}
            </span>
          </div>
          <div className="engine-status-row">
            <span>ENVIRONMENT</span>
            <span style={{ color: 'var(--text-secondary)' }}>LOCAL DEV</span>
          </div>
        </div>
      </aside>

      {/* ============================================================ */}
      {/* MAIN WORKSPACE WRAPPER                                       */}
      {/* ============================================================ */}
      <div className="main-wrapper">
        {/* Top Control & Telemetry Bar */}
        <header className="top-bar">
          <div className="breadcrumbs">
            <span>SENTINEL</span>
            <span>/</span>
            <span className="breadcrumb-active">{activeTab.toUpperCase().replace('_', ' ')}</span>
            {activeRunId && (
              <>
                <span>/</span>
                <span style={{ color: 'var(--accent)' }}>RUN-{activeRunId.slice(0, 8)}</span>
              </>
            )}
          </div>

          <div className="top-bar-telemetry">
            {searchMode === 'ddg' && (
              <span className="pill pill-info" style={{ border: '1px solid rgba(0, 217, 255, 0.4)' }}>
                MODE: DUCKDUCKGO LIVE
              </span>
            )}
            {searchMode === 'live' && (
              <span className="pill pill-success">
                MODE: TAVILY LIVE
              </span>
            )}
            {searchMode === 'fixture' && (
              <span className="pill pill-warning">
                MODE: SIMULATED FIXTURE
              </span>
            )}

            <span className="pill pill-neutral" style={{ fontFamily: 'var(--font-mono)' }}>
              127.0.0.1:8000
            </span>

            {activeTab !== 'new_investigation' && (
              <button
                className="btn btn-primary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                onClick={() => setActiveTab('new_investigation')}
              >
                + New Investigation
              </button>
            )}
          </div>
        </header>

        {/* Global Error Banner */}
        {investigationError && (
          <div style={{ padding: '0.75rem 1.5rem', background: 'rgba(255, 90, 90, 0.1)', borderBottom: '1px solid rgba(255, 90, 90, 0.3)', color: 'var(--error)', fontSize: '0.85rem' }}>
            <strong>Investigation Pipeline Alert:</strong> {investigationError}
          </div>
        )}

        {/* Viewport Content */}
        <main className="content-viewport">
          {/* ============================================================== */}
          {/* VIEW 1: INVESTIGATIONS LIST TABLE                              */}
          {/* ============================================================== */}
          {activeTab === 'investigations' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                    Investigation Telemetry Registry
                  </h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', marginTop: '0.2rem' }}>
                    Persisted multi-source investigations with deterministic quote verification and policy adjudication.
                  </p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => setActiveTab('new_investigation')}
                >
                  Start New Investigation
                </button>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title">Recent Investigation Runs</span>
                  <span className="pill pill-neutral">{investigationsList.length} Total Runs</span>
                </div>
                <div className="card-body" style={{ padding: 0 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Run ID</th>
                        <th>Supplier</th>
                        <th>Search Mode</th>
                        <th>Pipeline Status</th>
                        <th>Created At</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {investigationsList.map((r) => {
                        const sup = suppliersData?.items.find((s) => s.id === r.supplier_id)
                        const runMode = (r.metrics_json as Record<string, unknown>)?.search_mode || 'fixture'
                        return (
                          <tr key={r.id}>
                            <td>
                              <code style={{ color: 'var(--accent)' }}>{r.id.slice(0, 8)}</code>
                            </td>
                            <td>
                              <strong style={{ color: 'var(--text-primary)' }}>{sup?.name || r.supplier_id.slice(0, 8)}</strong>
                              {sup?.country_or_region && (
                                <span style={{ marginLeft: '0.4rem', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                                  ({sup.country_or_region})
                                </span>
                              )}
                            </td>
                            <td>
                              {runMode === 'ddg' ? (
                                <span className="pill pill-info">DuckDuckGo Live</span>
                              ) : runMode === 'live' ? (
                                <span className="pill pill-success">Tavily Live</span>
                              ) : (
                                <span className="pill pill-warning">Simulated Fixture</span>
                              )}
                            </td>
                            <td>
                              <span
                                className={`pill ${
                                  r.status === 'completed'
                                    ? 'pill-success'
                                    : r.status === 'failed'
                                    ? 'pill-danger'
                                    : 'pill-info'
                                }`}
                              >
                                {r.status.toUpperCase()}
                              </span>
                            </td>
                            <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                              {new Date(r.created_at).toLocaleString()}
                            </td>
                            <td>
                              <button
                                className="btn btn-outline"
                                style={{ padding: '0.25rem 0.65rem', fontSize: '0.8rem' }}
                                onClick={() => navigateToRun(r)}
                              >
                                Open Workspace →
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                      {investigationsList.length === 0 && !isListLoading && (
                        <tr>
                          <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                            No investigations logged yet. Click "Start New Investigation" above to initiate one.
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
          {/* VIEW 2: NEW INVESTIGATION INTAKE (REAL LOCAL WORKFLOW)        */}
          {/* ============================================================== */}
          {activeTab === 'new_investigation' && (
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Initiate Supplier Incident Investigation
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.86rem', marginTop: '0.2rem' }}>
                  Execute real-time public discovery, local Ollama claim extraction, and deterministic policy rulebook evaluation.
                </p>
              </div>

              {/* Mode Control Card */}
              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title">Search & Discovery Engine</span>
                  <span className="pill pill-info">Source Provider Selection</span>
                </div>
                <div className="card-body">
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                    <label
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.65rem',
                        padding: '0.85rem',
                        border: `1px solid ${searchMode === 'ddg' ? 'var(--accent)' : 'var(--border)'}`,
                        borderRadius: 'var(--radius-sm)',
                        background: searchMode === 'ddg' ? 'rgba(0, 217, 255, 0.05)' : 'var(--surface-elevated)',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="radio"
                        name="modeChoice"
                        value="ddg"
                        checked={searchMode === 'ddg'}
                        onChange={() => setSearchMode('ddg')}
                        style={{ marginTop: '0.25rem' }}
                      />
                      <div>
                        <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>DuckDuckGo Live Search</strong>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          Primary live engine. Discovers live public news & articles without external API keys.
                        </div>
                      </div>
                    </label>

                    <label
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.65rem',
                        padding: '0.85rem',
                        border: `1px solid ${searchMode === 'live' ? 'var(--accent)' : 'var(--border)'}`,
                        borderRadius: 'var(--radius-sm)',
                        background: searchMode === 'live' ? 'rgba(0, 217, 255, 0.05)' : 'var(--surface-elevated)',
                        cursor: isTavilyAvailable ? 'pointer' : 'not-allowed',
                        opacity: isTavilyAvailable ? 1 : 0.5,
                      }}
                    >
                      <input
                        type="radio"
                        name="modeChoice"
                        value="live"
                        checked={searchMode === 'live'}
                        onChange={() => isTavilyAvailable && setSearchMode('live')}
                        disabled={!isTavilyAvailable}
                        style={{ marginTop: '0.25rem' }}
                      />
                      <div>
                        <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>Tavily Live Web Search</strong>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          {isTavilyAvailable
                            ? 'Cloud-indexed technical search enabled.'
                            : 'Set TAVILY_API_KEY in .env to enable.'}
                        </div>
                      </div>
                    </label>

                    <label
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.65rem',
                        padding: '0.85rem',
                        border: `1px solid ${searchMode === 'fixture' ? 'var(--warning)' : 'var(--border)'}`,
                        borderRadius: 'var(--radius-sm)',
                        background: searchMode === 'fixture' ? 'rgba(255, 181, 71, 0.05)' : 'var(--surface-elevated)',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="radio"
                        name="modeChoice"
                        value="fixture"
                        checked={searchMode === 'fixture'}
                        onChange={() => setSearchMode('fixture')}
                        style={{ marginTop: '0.25rem' }}
                      />
                      <div>
                        <strong style={{ color: 'var(--warning)', fontSize: '0.9rem' }}>Simulated Fixture Mode</strong>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          Deterministic offline fixtures for evaluation and synthetic testing.
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Investigation Target Form */}
              <form onSubmit={handleStartCustomInvestigation}>
                <div className="card" style={{ marginBottom: '1.25rem' }}>
                  <div className="card-header">
                    <span className="card-title">Target Supplier Profile</span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        type="button"
                        className={`btn ${formSupplierMode === 'new' ? 'btn-primary' : 'btn-outline'}`}
                        style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}
                        onClick={() => setFormSupplierMode('new')}
                      >
                        + New Supplier
                      </button>
                      <button
                        type="button"
                        className={`btn ${formSupplierMode === 'existing' ? 'btn-primary' : 'btn-outline'}`}
                        style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}
                        onClick={() => setFormSupplierMode('existing')}
                      >
                        Select Existing
                      </button>
                    </div>
                  </div>

                  <div className="card-body">
                    {formSupplierMode === 'existing' ? (
                      <div className="form-group">
                        <label className="form-label">Select Registered Supplier:</label>
                        <select
                          className="form-select"
                          value={formExistingSupplierId}
                          onChange={(e) => setFormExistingSupplierId(e.target.value)}
                          required
                        >
                          <option value="">Choose a registered supplier…</option>
                          {suppliersData?.items.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} ({s.country_or_region || 'Unknown Country'}) — Criticality: {s.criticality}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <>
                        <div className="grid-2">
                          <div className="form-group">
                            <label className="form-label">Supplier Corporate Name *</label>
                            <input
                              type="text"
                              className="form-input"
                              placeholder="e.g. BASF SE, TSMC, or Micron Technology"
                              value={formName}
                              onChange={(e) => setFormName(e.target.value)}
                              required
                            />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Country / Jurisdiction</label>
                            <input
                              type="text"
                              className="form-input"
                              placeholder="e.g. Germany, Taiwan, or United States"
                              value={formCountry}
                              onChange={(e) => setFormCountry(e.target.value)}
                            />
                          </div>
                        </div>

                        <div className="grid-2">
                          <div className="form-group">
                            <label className="form-label">Official Domain (for Entity Resolution)</label>
                            <input
                              type="text"
                              className="form-input"
                              placeholder="e.g. basf.com or tsmc.com"
                              value={formDomain}
                              onChange={(e) => setFormDomain(e.target.value)}
                            />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Criticality Tier</label>
                            <select
                              className="form-select"
                              value={formCriticality}
                              onChange={(e) => setFormCriticality(e.target.value as any)}
                            >
                              <option value="high">High Criticality (Tier 1)</option>
                              <option value="medium">Medium Criticality (Tier 2)</option>
                              <option value="low">Low Criticality (Tier 3)</option>
                              <option value="unknown">Unknown</option>
                            </select>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Buyer Exposure Context */}
                <div className="card" style={{ marginBottom: '1.25rem' }}>
                  <div className="card-header">
                    <span className="card-title">Buyer Inventory & Recovery Context (Optional)</span>
                    <span className="pill pill-neutral">Formula EX-003</span>
                  </div>
                  <div className="card-body">
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
                      Operational gap is calculated deterministically as <code>Gap = max(0, Disruption - Coverage)</code>. Missing fields remain unknown without being fabricated.
                    </p>
                    <div className="grid-3">
                      <div className="form-group">
                        <label className="form-label">Critical Part / Component Name</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Electronic Chemical Precursor"
                          value={formPartName}
                          onChange={(e) => setFormPartName(e.target.value)}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Inventory Coverage (Days)</label>
                        <input
                          type="number"
                          className="form-input"
                          placeholder="e.g. 14"
                          value={formCoverageDays}
                          onChange={(e) => setFormCoverageDays(e.target.value)}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Expected Recovery (Days)</label>
                        <input
                          type="number"
                          className="form-input"
                          placeholder="e.g. 45"
                          value={formRecoveryDays}
                          onChange={(e) => setFormRecoveryDays(e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Categories Allowlist */}
                <div className="card" style={{ marginBottom: '1.5rem' }}>
                  <div className="card-header">
                    <span className="card-title">Incident Category Filters</span>
                    <span className="pill pill-neutral">Allowlist Verified</span>
                  </div>
                  <div className="card-body">
                    <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                      {[
                        { id: 'operational_disruption', label: 'Operational Disruption (Fire, Power, Outage)' },
                        { id: 'environmental_regulatory', label: 'Environmental & Regulatory (EPA, Sanctions)' },
                        { id: 'logistics_disruption', label: 'Logistics Disruption (Port, Freight, Rail)' },
                      ].map((cat) => (
                        <label key={cat.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={formCategories.includes(cat.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setFormCategories([...formCategories, cat.id])
                              } else {
                                setFormCategories(formCategories.filter((c) => c !== cat.id))
                              }
                            }}
                          />
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{cat.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => setActiveTab('investigations')}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ padding: '0.65rem 1.75rem', fontSize: '0.92rem' }}
                    disabled={launchMutation.isPending}
                  >
                    {launchMutation.isPending ? 'Executing Investigation Pipeline…' : 'Start Live Investigation →'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ============================================================== */}
          {/* VIEW 3: SPLIT INVESTIGATION WORKSPACE                          */}
          {/* ============================================================== */}
          {activeTab === 'workspace' && (
            <div>
              {!activeRunId ? (
                <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                  <h3 style={{ color: 'var(--text-primary)', fontSize: '1.25rem' }}>No Active Investigation Selected</h3>
                  <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
                    Select an investigation from the registry or launch a new real-time investigation.
                  </p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('new_investigation')}>
                    + Launch New Investigation
                  </button>
                </div>
              ) : (
                <div className="workspace-grid">
                  {/* ---------------------------------------------------- */}
                  {/* MAIN COLUMN (65%): CLAIMS, QUOTES, REAL SOURCES      */}
                  {/* ---------------------------------------------------- */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Investigation Run Status Banner */}
                    <div className="card">
                      <div className="card-header">
                        <div>
                          <span className="card-title">Run ID: {run?.id}</span>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                            Supplier: <strong style={{ color: 'var(--text-primary)' }}>{selectedSupplier?.name || run?.supplier_id}</strong> | Engine: <code>{providersHealth?.llm?.model_id || 'qwen3.5:9b'}</code>
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
                          {(run?.metrics_json as Record<string, unknown>)?.search_mode === 'fixture' && (
                            <span className="pill pill-warning">Simulated Fixture</span>
                          )}
                          {(run?.metrics_json as Record<string, unknown>)?.search_mode === 'ddg' && (
                            <span className="pill pill-info">DuckDuckGo Live</span>
                          )}
                        </div>
                      </div>

                      {isRunLoading && (
                        <div className="card-body">
                          <div style={{ color: 'var(--accent)', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span
                              style={{
                                display: 'inline-block',
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                background: 'var(--accent)',
                                animation: 'pulse 1.5s infinite',
                              }}
                            />
                            Pipeline active: executing search retrieval, local Ollama claim extraction, and deterministic resolution…
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Section: Extracted Claims & Verbatim Evidence (Rule E-005) */}
                    <div className="card">
                      <div className="card-header">
                        <span className="card-title">Extracted Incident Claims & Verbatim Quotes</span>
                        <span className="pill pill-neutral">{claims.length} Claims Extracted</span>
                      </div>
                      <div className="card-body">
                        {claims.length === 0 && !isRunLoading && (
                          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem' }}>
                            No discrete incident claims extracted for this supplier run.
                          </p>
                        )}

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          {claims.map((claim) => {
                            const isVerified = claim.extraction_status === 'validated'
                            const sourceDoc = sources.find((s) => s.id === claim.source_id)

                            return (
                              <div
                                key={claim.id}
                                style={{
                                  border: '1px solid var(--border)',
                                  borderRadius: 'var(--radius-sm)',
                                  padding: '1rem',
                                  background: 'var(--surface-elevated)',
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <div>
                                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                                      {claim.subject_text}
                                    </div>
                                    <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                                      <strong>Claimed Event:</strong> {claim.object_text}
                                    </div>
                                  </div>
                                  <span className={`pill ${isVerified ? 'pill-success' : 'pill-danger'}`}>
                                    {isVerified ? 'VERIFIED EXACT (Rule E-005)' : 'QUOTE MISMATCH'}
                                  </span>
                                </div>

                                {/* Verbatim Quote Highlight */}
                                <div style={{ marginTop: '0.65rem' }}>
                                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.2rem' }}>
                                    Literal Supporting Quotation:
                                  </div>
                                  <div
                                    className={`quote-box ${isVerified ? 'quote-verified' : 'quote-mismatch'}`}
                                    style={{ margin: 0, fontSize: '0.84rem' }}
                                  >
                                    "{claim.supporting_quote}"
                                  </div>
                                </div>

                                {sourceDoc && (
                                  <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span>
                                      Source: <strong style={{ color: 'var(--text-secondary)' }}>{sourceDoc.publisher_name || sourceDoc.domain}</strong> | Event Date: {claim.event_date || 'Unknown'}
                                    </span>
                                    <a
                                      href={sourceDoc.url_original}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{ color: 'var(--accent)', textDecoration: 'none' }}
                                    >
                                      Open Source ↗
                                    </a>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    </div>

                    {/* Section: Discovered Public Sources */}
                    <div className="card">
                      <div className="card-header">
                        <span className="card-title">Discovered Evidence Sources</span>
                        <span className="pill pill-neutral">{sources.length} Documents</span>
                      </div>
                      <div className="card-body" style={{ padding: 0 }}>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>Publisher / Domain</th>
                              <th>Published</th>
                              <th>Content Status</th>
                              <th>Source URL</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sources.map((src) => (
                              <tr key={src.id}>
                                <td>
                                  <strong style={{ color: 'var(--text-primary)' }}>{src.publisher_name || src.domain}</strong>
                                </td>
                                <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                  {src.published_at ? new Date(src.published_at).toLocaleDateString() : 'Unknown'}
                                </td>
                                <td>
                                  <span
                                    className={`pill ${
                                      src.content_status === 'available'
                                        ? 'pill-success'
                                        : src.content_status === 'snippet_only'
                                        ? 'pill-warning'
                                        : 'pill-neutral'
                                    }`}
                                  >
                                    {src.content_status}
                                  </span>
                                </td>
                                <td>
                                  <a
                                    href={src.url_original}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                                  >
                                    <span>{src.domain || 'External Link'}</span>
                                    <span>↗</span>
                                  </a>
                                </td>
                              </tr>
                            ))}
                            {sources.length === 0 && !isRunLoading && (
                              <tr>
                                <td colSpan={4} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                                  No external sources retrieved.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Section: Source Lineage Matrix */}
                    {relations.length > 0 && (
                      <div className="card">
                        <div className="card-header">
                          <span className="card-title">Source Lineage & Syndication Relations</span>
                          <span className="pill pill-warning">{relations.length} Pairs Clustered</span>
                        </div>
                        <div className="card-body">
                          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                            Syndicated wire reports sharing identical textual lineage are deduplicated to prevent artificial confirmation bias.
                          </p>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {relations.map((rel) => (
                              <div
                                key={rel.id}
                                style={{
                                  padding: '0.65rem 0.85rem',
                                  background: 'var(--surface-elevated)',
                                  border: '1px solid var(--border)',
                                  borderRadius: 'var(--radius-xs)',
                                  fontSize: '0.82rem',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                }}
                              >
                                <div>
                                  <code>{rel.source_a_id.slice(0, 8)}</code> ↔ <code>{rel.source_b_id.slice(0, 8)}</code>:{' '}
                                  <span style={{ color: 'var(--text-secondary)' }}>
                                    {String((rel.evidence as Record<string, unknown>)?.observation || rel.relation)}
                                  </span>
                                </div>
                                <span className="pill pill-warning">{rel.relation}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* ---------------------------------------------------- */}
                  {/* SECONDARY COLUMN (35%): RESOLUTION, POLICY, GATE     */}
                  {/* ---------------------------------------------------- */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Entity Resolution Card */}
                    <div className="card">
                      <div className="card-header">
                        <span className="card-title">Entity Resolution</span>
                        <span className="pill pill-neutral">Rules ID-001–005</span>
                      </div>
                      <div className="card-body">
                        {activeIncident ? (
                          <div style={{ fontSize: '0.85rem', lineHeight: 1.8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <strong style={{ color: 'var(--text-secondary)' }}>Match Status:</strong>
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
                                {activeIncident.entity_match_status.toUpperCase()}
                              </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <strong style={{ color: 'var(--text-secondary)' }}>Event Type:</strong>
                              <code>{activeIncident.event_type}</code>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <strong style={{ color: 'var(--text-secondary)' }}>Facility Location:</strong>
                              <span style={{ color: 'var(--text-primary)' }}>{activeIncident.facility_location || 'Not Specified'}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <strong style={{ color: 'var(--text-secondary)' }}>Independent Sources:</strong>
                              <span style={{ color: 'var(--text-primary)' }}>
                                {activeIncident.independent_support_count ?? sources.length} Groups
                              </span>
                            </div>
                          </div>
                        ) : (
                          <p style={{ color: 'var(--text-muted)' }}>No candidate incident active.</p>
                        )}
                      </div>
                    </div>

                    {/* Deterministic Exposure Card */}
                    <div className="card">
                      <div className="card-header">
                        <span className="card-title">Deterministic Exposure</span>
                        <span className="pill pill-neutral">Formula EX-003</span>
                      </div>
                      <div className="card-body">
                        {(() => {
                          const inputVals = activeIncident?.exposure?.input_values_json as
                            | Record<string, { value?: unknown }>
                            | undefined
                          const dur = inputVals?.disruption_duration_days?.value
                          const cov = inputVals?.inventory_coverage_days?.value
                          const gap = activeIncident?.exposure?.potential_inventory_gap_days

                          return (
                            <div style={{ fontSize: '0.85rem', lineHeight: 1.8 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <strong style={{ color: 'var(--text-secondary)' }}>Disruption Duration:</strong>
                                <span style={{ color: 'var(--text-primary)' }}>
                                  {dur !== undefined && dur !== null ? `${String(dur)} Days` : 'UNKNOWN'}
                                </span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <strong style={{ color: 'var(--text-secondary)' }}>Inventory Coverage:</strong>
                                <span style={{ color: 'var(--text-primary)' }}>
                                  {cov !== undefined && cov !== null ? `${String(cov)} Days` : 'UNKNOWN'}
                                </span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
                                <strong style={{ color: 'var(--text-secondary)' }}>Operational Gap:</strong>
                                <strong style={{ color: gap && Number(gap) > 0 ? 'var(--error)' : 'var(--accent)', fontSize: '0.95rem' }}>
                                  {gap !== null && gap !== undefined ? `${gap} DAYS` : 'UNKNOWN / UNASSESSED'}
                                </strong>
                              </div>
                            </div>
                          )
                        })()}
                      </div>
                    </div>

                    {/* Policy Rulebook Recommendation */}
                    <div className="card">
                      <div className="card-header">
                        <span className="card-title">Policy Recommendation</span>
                        <span className="pill pill-neutral">Rulebook Gate</span>
                      </div>
                      <div className="card-body">
                        {activeIncident?.policy_decision ? (
                          <div>
                            <div style={{ marginBottom: '0.75rem' }}>
                              <span
                                className={`pill ${
                                  activeIncident.policy_decision.recommendation === 'urgent_human_review'
                                    ? 'pill-danger'
                                    : activeIncident.policy_decision.recommendation === 'request_supplier_confirmation'
                                    ? 'pill-warning'
                                    : 'pill-info'
                                }`}
                                style={{ fontSize: '0.85rem', padding: '0.35rem 0.75rem', width: '100%', textAlign: 'center', display: 'block' }}
                              >
                                {activeIncident.policy_decision.recommendation.replace(/_/g, ' ').toUpperCase()}
                              </span>
                            </div>

                            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                              {activeIncident.policy_decision.reasons?.map((r, i) => (
                                <div key={i} style={{ marginBottom: '0.35rem' }}>• {r}</div>
                              ))}
                            </div>

                            {activeIncident.policy_decision.rule_ids_fired && (
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                Triggered: {activeIncident.policy_decision.rule_ids_fired.join(', ')}
                              </div>
                            )}
                          </div>
                        ) : (
                          <p style={{ color: 'var(--text-muted)' }}>No policy decision evaluated.</p>
                        )}
                      </div>
                    </div>

                    {/* Integrated Human Review Decision Gate */}
                    {activeIncident && (
                      <div className="card">
                        <div className="card-header">
                          <span className="card-title">Human Decision Gate</span>
                          <span className={`pill ${activeIncident.review_required ? 'pill-danger' : 'pill-success'}`}>
                            {activeIncident.review_required ? 'Signoff Required' : 'Disposed'}
                          </span>
                        </div>
                        <div className="card-body">
                          <form
                            onSubmit={(e) => {
                              e.preventDefault()
                              reviewMutation.mutate()
                            }}
                          >
                            <div className="form-group">
                              <label className="form-label">Reviewer Disposition:</label>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                                {[
                                  { id: 'approve_recommendation', label: 'Accept Automated Recommendation' },
                                  { id: 'request_more_information', label: 'Request Supplier Confirmation' },
                                  { id: 'mark_monitor_only', label: 'Mark as Monitor Only' },
                                  { id: 'reject_recommendation', label: 'Override / Reject Policy Action' },
                                ].map((act) => (
                                  <label key={act.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.82rem' }}>
                                    <input
                                      type="radio"
                                      name="disposition"
                                      value={act.id}
                                      checked={decisionAction === act.id}
                                      onChange={() => setDecisionAction(act.id as any)}
                                    />
                                    <span style={{ color: 'var(--text-primary)' }}>{act.label}</span>
                                  </label>
                                ))}
                              </div>
                            </div>

                            {(decisionAction === 'reject_recommendation' || decisionAction === 'mark_monitor_only') && (
                              <div className="form-group">
                                <label className="form-label">Override Target:</label>
                                <select
                                  className="form-select"
                                  value={overrideRec}
                                  onChange={(e) => setOverrideRec(e.target.value as any)}
                                  required
                                >
                                  <option value="">Select target recommendation…</option>
                                  <option value="monitor">Monitor Only</option>
                                  <option value="request_supplier_confirmation">Request Supplier Confirmation</option>
                                  <option value="review_contingency_plan">Review Contingency Plan</option>
                                  <option value="urgent_human_review">Urgent Human Review</option>
                                </select>
                              </div>
                            )}

                            <div className="form-group">
                              <label className="form-label">Reviewer ID / Title</label>
                              <input
                                type="text"
                                className="form-input"
                                value={reviewerName}
                                onChange={(e) => setReviewerName(e.target.value)}
                                required
                              />
                            </div>

                            <div className="form-group">
                              <label className="form-label">Reviewer Audit Rationale</label>
                              <textarea
                                className="form-textarea"
                                rows={2}
                                value={reviewerNote}
                                onChange={(e) => setReviewerNote(e.target.value)}
                                placeholder="State justification for disposition or override…"
                              />
                            </div>

                            {decisionFeedback && (
                              <div
                                style={{
                                  padding: '0.5rem 0.75rem',
                                  borderRadius: 'var(--radius-xs)',
                                  background: decisionFeedback.type === 'success' ? 'rgba(0, 217, 255, 0.1)' : 'rgba(255, 90, 90, 0.1)',
                                  color: decisionFeedback.type === 'success' ? 'var(--accent)' : 'var(--error)',
                                  fontSize: '0.78rem',
                                  marginBottom: '0.75rem',
                                }}
                              >
                                {decisionFeedback.msg}
                              </div>
                            )}

                            <button
                              type="submit"
                              className="btn btn-primary"
                              style={{ width: '100%', padding: '0.55rem' }}
                              disabled={reviewMutation.isPending}
                            >
                              {reviewMutation.isPending ? 'Logging Signoff…' : 'Sign Off & Log to Ledger'}
                            </button>
                          </form>

                          {reviews.length > 0 && (
                            <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
                              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                                Past Signoffs ({reviews.length})
                              </div>
                              {reviews.map((rev) => (
                                <div key={rev.id} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                  <strong>{rev.reviewer_name}</strong>: {rev.action} ({new Date(rev.reviewed_at).toLocaleDateString()})
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ============================================================== */}
          {/* VIEW 4: SUPPLIER REGISTRY                                      */}
          {/* ============================================================== */}
          {activeTab === 'suppliers' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Supplier Registry & Exposure Profiles
                  </h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                    Registered supply chain nodes with verified domains and operational dependencies.
                  </p>
                </div>
                <button className="btn btn-primary" onClick={() => setActiveTab('new_investigation')}>
                  + Add Supplier
                </button>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title">Registered Suppliers</span>
                  <span className="pill pill-neutral">{suppliersData?.total || 0} Registered</span>
                </div>
                <div className="card-body" style={{ padding: 0 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Supplier Name</th>
                        <th>Region</th>
                        <th>Criticality</th>
                        <th>Registered Date</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {suppliersData?.items.map((sup) => (
                        <tr key={sup.id}>
                          <td>
                            <strong style={{ color: 'var(--text-primary)' }}>{sup.name}</strong>
                            {sup.aliases.length > 0 && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                Aliases: {sup.aliases.join(', ')}
                              </div>
                            )}
                          </td>
                          <td style={{ color: 'var(--text-secondary)' }}>{sup.country_or_region || 'Unknown'}</td>
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
                              {sup.criticality.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                            {new Date(sup.created_at).toLocaleDateString()}
                          </td>
                          <td>
                            <button
                              className="btn btn-primary"
                              style={{ padding: '0.25rem 0.65rem', fontSize: '0.78rem' }}
                              onClick={() => {
                                setSelectedSupplier(sup as any)
                                launchMutation.mutate({ supplierId: sup.id, mode: searchMode })
                              }}
                            >
                              Investigate Now
                            </button>
                          </td>
                        </tr>
                      ))}
                      {(!suppliersData || suppliersData.items.length === 0) && (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                            No suppliers registered yet.
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
          {/* VIEW 5: EVIDENCE & QUOTE INSPECTOR                             */}
          {/* ============================================================== */}
          {activeTab === 'evidence' && (
            <div>
              <div style={{ marginBottom: '1.25rem' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Deep Evidence Inspector
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                  Mathematical quote substring verification against stored immutable source documents (Rule E-005).
                </p>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title">Claims & Provenance Ledger</span>
                  <span className="pill pill-neutral">{claims.length} Claims</span>
                </div>
                <div className="card-body">
                  {claims.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                      No claims loaded. Open an investigation run from the Investigations list.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {claims.map((claim) => {
                        const isVerified = claim.extraction_status === 'validated'
                        const src = sources.find((s) => s.id === claim.source_id)

                        return (
                          <div
                            key={claim.id}
                            style={{
                              border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)',
                              padding: '1rem',
                              background: 'var(--surface-elevated)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <strong style={{ color: 'var(--text-primary)' }}>{claim.subject_text}</strong>
                              <span className={`pill ${isVerified ? 'pill-success' : 'pill-danger'}`}>
                                {isVerified ? 'VERIFIED EXACT (Rule E-005)' : 'QUOTE MISMATCH'}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                              Claimed Event: {claim.object_text}
                            </div>
                            <div className={`quote-box ${isVerified ? 'quote-verified' : 'quote-mismatch'}`} style={{ margin: '0.5rem 0' }}>
                              "{claim.supporting_quote}"
                            </div>
                            {src && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                                <span>Publisher: {src.publisher_name || src.domain}</span>
                                <a href={src.url_original} target="_blank" rel="noopener noreferrer">
                                  {src.url_original.slice(0, 50)}… ↗
                                </a>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* VIEW 6: AUDIT LEDGER                                           */}
          {/* ============================================================== */}
          {activeTab === 'audit' && (
            <div>
              <div style={{ marginBottom: '1.25rem' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Immutable Audit Ledger
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                  Cryptographically structured audit trail recording all human dispositions, overrides, and policy evaluations.
                </p>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title">Event Ledger</span>
                  <span className="pill pill-neutral">{auditEvents.length} Events</span>
                </div>
                <div className="card-body" style={{ padding: 0 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Event Type</th>
                        <th>Entity</th>
                        <th>Event Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditEvents.map((evt) => (
                        <tr key={evt.id}>
                          <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {new Date(evt.created_at).toLocaleString()}
                          </td>
                          <td>
                            <span className="pill pill-info">{evt.event_type}</span>
                          </td>
                          <td style={{ color: 'var(--text-secondary)' }}>{evt.entity_type}</td>
                          <td>
                            <code style={{ fontSize: '0.76rem' }}>
                              {JSON.stringify(evt.data).slice(0, 110)}
                              {JSON.stringify(evt.data).length > 110 ? '…' : ''}
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
            </div>
          )}

          {/* ============================================================== */}
          {/* VIEW 7: SYSTEM TELEMETRY                                       */}
          {/* ============================================================== */}
          {activeTab === 'telemetry' && (
            <div style={{ maxWidth: '800px' }}>
              <div style={{ marginBottom: '1.25rem' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  System & Provider Diagnostics
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                  Live infrastructure telemetry verifying local inference and discovery readiness.
                </p>
              </div>

              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title">LLM Inference Node</span>
                  <span className="pill pill-success">Configured</span>
                </div>
                <div className="card-body">
                  <div style={{ fontSize: '0.86rem', lineHeight: 2 }}>
                    <div><strong>Provider:</strong> <code>{providersHealth?.llm?.provider_name || 'ollama'}</code></div>
                    <div><strong>Active Model:</strong> <code>{providersHealth?.llm?.model_id || 'qwen3.5:9b'}</code></div>
                    <div><strong>Endpoint:</strong> <code>http://localhost:11434</code></div>
                    <div><strong>Architecture:</strong> Local Ollama on CPU / CUDA</div>
                  </div>
                </div>
              </div>

              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title">Public Web Search & Content Retrieval</span>
                  <span className="pill pill-info">Active</span>
                </div>
                <div className="card-body">
                  <div style={{ fontSize: '0.86rem', lineHeight: 2 }}>
                    <div>
                      <strong>Primary Live Search:</strong>{' '}
                      <code>DuckDuckGo Search (News & Text API)</code>
                    </div>
                    <div>
                      <strong>Content Extractor:</strong>{' '}
                      <code>Direct HTTP Client + BeautifulSoup Sanitizer</code>
                    </div>
                    <div>
                      <strong>Tavily Cloud Integration:</strong>{' '}
                      <code>{isTavilyAvailable ? 'Configured' : 'Not Configured (Optional)'}</code>
                    </div>
                    <div>
                      <strong>Safety Guardrails:</strong>{' '}
                      Max 6 searches per run, max 8 results, max 12,000 characters per document
                    </div>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title">Database & Core Application</span>
                  <span className={`pill ${health?.status === 'ok' ? 'pill-success' : 'pill-danger'}`}>
                    {health?.status.toUpperCase()}
                  </span>
                </div>
                <div className="card-body">
                  <div style={{ fontSize: '0.86rem', lineHeight: 2 }}>
                    <div><strong>Version:</strong> {health?.version || '0.1.0'}</div>
                    <div><strong>Environment:</strong> {health?.environment || 'development'}</div>
                    <div><strong>Database Status:</strong> {health?.database?.ok ? 'Connected (SQLite async)' : 'Degraded'}</div>
                    <div><strong>Last Heartbeat:</strong> {health?.timestamp || 'Just now'}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
