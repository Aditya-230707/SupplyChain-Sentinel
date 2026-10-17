import type {
  InvestigationRun,
  Supplier,
  IncidentCandidate,
  Claim,
  SourceDocument,
  SourceRelation,
  HumanReview,
  HumanReviewAction,
  PolicyRecommendation,
} from '../lib/api'

interface WorkspaceViewProps {
  run: InvestigationRun | null | undefined
  supplier: Supplier | null
  activeIncident: IncidentCandidate | undefined
  claims: Claim[]
  sources: SourceDocument[]
  relations: SourceRelation[]
  reviews: HumanReview[]
  isRunLoading: boolean
  decisionAction: HumanReviewAction
  setDecisionAction: (action: HumanReviewAction) => void
  overrideRec: PolicyRecommendation | ''
  setOverrideRec: (rec: PolicyRecommendation | '') => void
  reviewerName: string
  setReviewerName: (name: string) => void
  reviewerNote: string
  setReviewerNote: (note: string) => void
  decisionFeedback: { type: 'success' | 'error'; msg: string } | null
  onSubmitDecision: () => void
  isReviewPending: boolean
  onNewInvestigation: () => void
  activeModelId?: string | null
}

export function WorkspaceView({
  run,
  supplier,
  activeIncident,
  claims,
  sources,
  relations,
  reviews,
  isRunLoading,
  decisionAction,
  setDecisionAction,
  overrideRec,
  setOverrideRec,
  reviewerName,
  setReviewerName,
  reviewerNote,
  setReviewerNote,
  decisionFeedback,
  onSubmitDecision,
  isReviewPending,
  onNewInvestigation,
  activeModelId,
}: WorkspaceViewProps) {
  if (!run) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h3 style={{ color: 'var(--text-primary)', fontSize: '1.25rem' }}>No Active Investigation Selected</h3>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
          Select an investigation from the registry or launch a new real-time investigation.
        </p>
        <button className="btn btn-primary" onClick={onNewInvestigation}>
          + Launch New Investigation
        </button>
      </div>
    )
  }

  const runMode = (run.metrics_json as Record<string, unknown>)?.search_mode || 'fixture'

  return (
    <div className="workspace-grid">
      {/* ---------------------------------------------------- */}
      {/* MAIN COLUMN (65%): CLAIMS, QUOTES, REAL SOURCES      */}
      {/* ---------------------------------------------------- */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Investigation Run Status Banner */}
        <div className="card">
          <div className="card-header">
            <div>
              <span className="card-title">Run ID: {run.id}</span>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Supplier: <strong style={{ color: 'var(--text-primary)' }}>{supplier?.name || run.supplier_id}</strong> | Engine: <code>{activeModelId || 'qwen3.5:9b'}</code>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <span
                className={`pill ${
                  run.status === 'completed'
                    ? 'pill-success'
                    : run.status === 'failed'
                    ? 'pill-danger'
                    : 'pill-info'
                }`}
              >
                {run.status.toUpperCase()}
              </span>
              {runMode === 'fixture' && (
                <span className="pill pill-warning">Simulated Fixture</span>
              )}
              {runMode === 'ddg' && (
                <span className="pill pill-info">DuckDuckGo Live</span>
              )}
              {runMode === 'live' && (
                <span className="pill pill-success">Tavily Live</span>
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
        {/* Evidence Graph & Provenance Integrity */}
        {(() => {
          const provenance = (run?.metrics_json as Record<string, unknown>)?.provenance as
            | {
                quote_integrity_ratio?: number
                source_independence_ratio?: number
                data_completeness_score?: number
                contradiction_count?: number
              }
            | undefined

          if (!provenance) return null

          return (
            <div className="card">
              <div className="card-header">
                <div>
                  <span className="card-title">Evidence DAG & Provenance</span>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Graph Integrity Verification</div>
                </div>
                <span className="pill pill-success">Bipartite DAG</span>
              </div>
              <div className="card-body">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.82rem' }}>
                  <div style={{ background: 'var(--surface-elevated)', padding: '0.5rem 0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Completeness</div>
                    <strong style={{ color: 'var(--accent)', fontSize: '0.95rem' }}>
                      {Math.round((provenance.data_completeness_score ?? 1) * 100)}%
                    </strong>
                  </div>
                  <div style={{ background: 'var(--surface-elevated)', padding: '0.5rem 0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Quote Integrity</div>
                    <strong style={{ color: 'var(--success)', fontSize: '0.95rem' }}>
                      {Math.round((provenance.quote_integrity_ratio ?? 1) * 100)}%
                    </strong>
                  </div>
                  <div style={{ background: 'var(--surface-elevated)', padding: '0.5rem 0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Independence</div>
                    <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                      {Math.round((provenance.source_independence_ratio ?? 1) * 100)}%
                    </strong>
                  </div>
                  <div style={{ background: 'var(--surface-elevated)', padding: '0.5rem 0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Contradictions</div>
                    <strong style={{ color: (provenance.contradiction_count ?? 0) > 0 ? 'var(--warning)' : 'var(--text-muted)', fontSize: '0.95rem' }}>
                      {provenance.contradiction_count ?? 0}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          )
        })()}

        {/* Next-Best-Investigation VOI Trace */}
        {(() => {
          const trace = (run?.metrics_json as Record<string, unknown>)?.investigation_trace as
            | {
                enabled?: boolean
                initial_recommendation?: string | null
                final_recommendation?: string | null
                recommendation_changed?: boolean
                identified_gaps?: Array<{
                  gap_type: string
                  description: string
                  impact_weight: number
                }>
                steps?: Array<{
                  step_number: number
                  query: string
                  targeted_gap: string
                  rationale: string
                  heuristic_score: number
                  new_sources_count: number
                  new_claims_count: number
                  prior_recommendation: string
                  new_recommendation: string
                  recommendation_changed: boolean
                  termination_reason?: string | null
                }>
              }
            | undefined

          if (!trace || !trace.enabled) return null

          return (
            <div className="card">
              <div className="card-header">
                <div>
                  <span className="card-title">Next-Best-Investigation</span>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    VOI Heuristic Information-Gain Trace
                  </div>
                </div>
                <span className={`pill ${trace.recommendation_changed ? 'pill-warning' : 'pill-info'}`}>
                  {trace.recommendation_changed ? 'POLICY SHIFTED' : 'CONFIRMED'}
                </span>
              </div>
              <div className="card-body" style={{ fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {trace.identified_gaps && trace.identified_gaps.length > 0 && (
                  <div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                      Identified Evidence Gaps:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                      {trace.identified_gaps.map((gap, i) => (
                        <div key={i} style={{ background: 'var(--surface-elevated)', padding: '0.35rem 0.5rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.76rem' }}>{gap.description}</span>
                          <span className="pill pill-neutral" style={{ fontSize: '0.68rem' }}>
                            w={(gap.impact_weight * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {trace.steps && trace.steps.length > 0 && (
                  <div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                      Executed Follow-up Query:
                    </div>
                    {trace.steps.map((step, i) => (
                      <div key={i} style={{ background: 'var(--surface-elevated)', padding: '0.5rem 0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--accent)', fontSize: '0.78rem' }}>Step #{step.step_number}</span>
                          <span className="pill pill-neutral" style={{ fontSize: '0.68rem' }}>
                            VOI: {step.heuristic_score}
                          </span>
                        </div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem', marginBottom: '0.3rem', wordBreak: 'break-all' }}>
                          <code>{step.query}</code>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                          <span>New Sources: <strong>{step.new_sources_count}</strong> | Claims: <strong>{step.new_claims_count}</strong></span>
                          <span style={{ color: step.recommendation_changed ? 'var(--warning)' : 'var(--accent)' }}>
                            {step.prior_recommendation} → {step.new_recommendation}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )
        })()}

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
                  onSubmitDecision()
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
                  disabled={isReviewPending}
                >
                  {isReviewPending ? 'Logging Signoff…' : 'Sign Off & Log to Ledger'}
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
  )
}
