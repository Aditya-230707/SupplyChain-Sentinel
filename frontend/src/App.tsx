// SupplyChain Sentinel Application View
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
import { Sidebar } from './components/Sidebar'
import type { ActiveTab } from './lib/constants'
import { TopBar } from './components/TopBar'
import { InvestigationsView } from './components/InvestigationsView'
import { NewInvestigationView } from './components/NewInvestigationView'
import { WorkspaceView } from './components/WorkspaceView'
import { SuppliersView } from './components/SuppliersView'
import { AuditView } from './components/AuditView'
import { DiagnosticsModal } from './components/DiagnosticsModal'

export default function App() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<ActiveTab>('investigations')
  const [searchMode, setSearchMode] = useState<'ddg' | 'live' | 'fixture'>('ddg')
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false)

  // Selected entities for active investigation workspace
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
      return data?.status &&
        ['queued', 'searching', 'extracting', 'resolving', 'adjudicating', 'assessing_impact'].includes(data.status)
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
    mutationFn: async ({
      supplierId,
      mode,
      categories,
    }: {
      supplierId: string
      mode: 'fixture' | 'live' | 'ddg'
      categories?: string[]
    }) => {
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
        decisionAction === 'reject_recommendation' ||
        decisionAction === 'mark_monitor_only' ||
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
        msg: 'Human decision recorded successfully and logged to the audit trail.',
      })
      queryClient.invalidateQueries({ queryKey: ['incident-reviews', activeIncident?.id] })
      queryClient.invalidateQueries({ queryKey: ['investigation-incidents', activeRunId] })
      queryClient.invalidateQueries({ queryKey: ['audit-events'] })
    },
    onError: (err: any) => {
      setDecisionFeedback({ type: 'error', msg: err.message || 'Failed to record decision' })
    },
  })

  // Handler: Start Custom Investigation from Intake Form
  const handleStartCustomInvestigation = async (params: {
    mode: 'ddg' | 'live' | 'fixture'
    supplierMode: 'existing' | 'new'
    existingSupplierId?: string
    name?: string
    country?: string
    domain?: string
    criticality: 'low' | 'medium' | 'high' | 'unknown'
    partName?: string
    coverage?: string
    recovery?: string
    categories: string[]
  }) => {
    setInvestigationError(null)

    try {
      let targetSupplierId = params.existingSupplierId || ''

      if (params.supplierMode === 'new') {
        if (!params.name?.trim()) {
          setInvestigationError('Supplier name is required.')
          return
        }
        const created = await createSupplier({
          name: params.name.trim(),
          country_or_region: params.country?.trim() || null,
          official_domains: params.domain?.trim() ? [params.domain.trim()] : [],
          criticality: params.criticality,
          parts: params.partName?.trim()
            ? [
                {
                  part_name: params.partName.trim(),
                  inventory_coverage_days: params.coverage?.trim() || null,
                  recovery_duration_days: params.recovery?.trim() || null,
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
        mode: params.mode,
        categories: params.categories,
      })
    } catch (err: any) {
      setInvestigationError(err.message || 'Failed to initiate investigation')
    }
  }

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
      {/* Persistent Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        investigationsCount={investigationsList.length}
        suppliersCount={suppliersData?.total || 0}
        auditCount={auditEvents.length}
        activeRunId={activeRunId}
        hasReviewRequired={Boolean(activeIncident?.review_required)}
        providersHealth={providersHealth}
        onNewInvestigation={() => setActiveTab('new_investigation')}
        onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <TopBar
          activeTab={activeTab}
          activeRunId={activeRunId}
          activeSupplierName={selectedSupplier?.name}
          searchMode={searchMode}
          onNavigateTab={setActiveTab}
          onNewInvestigation={() => setActiveTab('new_investigation')}
        />

        {investigationError && (
          <div
            style={{
              padding: '0.75rem 1.5rem',
              background: 'var(--status-urgent-bg)',
              borderBottom: '1px solid var(--status-urgent-border)',
              color: 'var(--status-urgent)',
              fontSize: '0.84rem',
            }}
          >
            <strong>Investigation Error:</strong> {investigationError}
          </div>
        )}

        <main className="content-viewport">
          {activeTab === 'investigations' && (
            <InvestigationsView
              investigations={investigationsList}
              suppliers={suppliersData?.items || []}
              isLoading={isListLoading}
              onSelectRun={navigateToRun}
              onNewInvestigation={() => setActiveTab('new_investigation')}
            />
          )}

          {activeTab === 'new_investigation' && (
            <NewInvestigationView
              searchMode={searchMode}
              setSearchMode={setSearchMode}
              suppliers={suppliersData?.items || []}
              isTavilyAvailable={isTavilyAvailable}
              onSubmit={handleStartCustomInvestigation}
              onCancel={() => setActiveTab('investigations')}
              isPending={launchMutation.isPending}
            />
          )}

          {activeTab === 'workspace' && (
            <WorkspaceView
              run={run}
              supplier={selectedSupplier}
              activeIncident={activeIncident}
              claims={claims}
              sources={sources}
              relations={relations}
              reviews={reviews}
              isRunLoading={isRunLoading}
              decisionAction={decisionAction}
              setDecisionAction={setDecisionAction}
              overrideRec={overrideRec}
              setOverrideRec={setOverrideRec}
              reviewerName={reviewerName}
              setReviewerName={setReviewerName}
              reviewerNote={reviewerNote}
              setReviewerNote={setReviewerNote}
              decisionFeedback={decisionFeedback}
              onSubmitDecision={() => reviewMutation.mutate()}
              isReviewPending={reviewMutation.isPending}
              onNewInvestigation={() => setActiveTab('new_investigation')}
              activeModelId={providersHealth?.llm?.model_id}
            />
          )}

          {activeTab === 'suppliers' && (
            <SuppliersView
              suppliers={suppliersData?.items || []}
              total={suppliersData?.total || 0}
              onInvestigate={(sup) => {
                setSelectedSupplier(sup as any)
                launchMutation.mutate({ supplierId: sup.id, mode: searchMode })
              }}
              onAddSupplier={() => setActiveTab('new_investigation')}
            />
          )}

          {activeTab === 'audit' && (
            <AuditView auditEvents={auditEvents} />
          )}
        </main>
      </div>

      {/* Diagnostics Modal */}
      <DiagnosticsModal
        isOpen={isDiagnosticsOpen}
        onClose={() => setIsDiagnosticsOpen(false)}
        health={health}
        providersHealth={providersHealth}
      />
    </div>
  )
}
