import { useState } from 'react'
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
}: WorkspaceViewProps) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
  const [evidenceFilter, setEvidenceFilter] = useState<'all' | 'claims' | 'sources'>('all')

  if (!run) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          No Active Investigation Selected
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto 1.5rem auto', fontSize: '0.86rem' }}>
          Select an investigation from the list to review evidence, assess operational gap, and record a decision.
        </p>
        <button className="btn btn-primary" onClick={onNewInvestigation} type="button">
          Start New Investigation
        </button>
      </div>
    )
  }

  const runMode = (run.metrics_json as Record<string, unknown>)?.search_mode || 'fixture'

  // Extract Operational Gap and Input Values
  const inputVals = activeIncident?.exposure?.input_values_json as
    | Record<string, { value?: unknown }>
    | undefined
  const disruptionDays = inputVals?.disruption_duration_days?.value
  const coverageDays = inputVals?.inventory_coverage_days?.value
  const inventoryGap = activeIncident?.exposure?.potential_inventory_gap_days

  const policyRec = activeIncident?.policy_decision?.recommendation
  const isReviewRequired = Boolean(activeIncident?.review_required)
  const isResolvedOrSignedOff = reviews.length > 0 && !isReviewRequired

  return (
    <div className="investigation-layout">
      {/* ==================================================== */}
      {/* LAYER 1: INVESTIGATION IDENTITY & CURRENT STATUS     */}
      {/* ==================================================== */}
      <div className="investigation-header-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <h1 style={{ fontSize: '1.35rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {supplier?.name || run.supplier_id}
              </h1>
              {supplier?.country_or_region && (
                <span className="badge badge-neutral" style={{ fontSize: '0.78rem' }}>
                  {supplier.country_or_region}
                </span>
              )}
              {supplier?.criticality && (
                <span
                  className={`badge ${
                    supplier.criticality === 'high'
                      ? 'badge-urgent'
                      : supplier.criticality === 'medium'
                      ? 'badge-caution'
                      : 'badge-neutral'
                  }`}
                  style={{ textTransform: 'capitalize' }}
                >
                  {supplier.criticality} Criticality
                </span>
              )}
            </div>

            <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span>
                <strong>Incident:</strong> {activeIncident?.event_type ? activeIncident.event_type.replace(/_/g, ' ') : 'Operational disruption report'}
              </span>
              {activeIncident?.facility_location && (
                <span>
                  <strong>Facility:</strong> {activeIncident.facility_location}
                </span>
              )}
              <span>
                <strong>Run ID:</strong> <code>{run.id.slice(0, 8)}</code>
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span
              className={`badge ${
                run.status === 'completed'
                  ? 'badge-verified'
                  : run.status === 'failed'
                  ? 'badge-urgent'
                  : 'badge-info'
              }`}
            >
              Status: {run.status.replace(/_/g, ' ')}
            </span>

            {runMode === 'ddg' ? (
              <span className="badge badge-info">DuckDuckGo Live</span>
            ) : runMode === 'live' ? (
              <span className="badge badge-verified">Tavily Live</span>
            ) : (
              <span className="badge badge-caution">Simulated Fixture</span>
            )}
          </div>
        </div>

        {/* Current Plain-Language Assessment Summary */}
        <div
          style={{
            padding: '0.85rem 1.15rem',
            borderRadius: 'var(--radius-md)',
            background:
              inventoryGap && Number(inventoryGap) > 0
                ? 'var(--status-urgent-bg)'
                : isResolvedOrSignedOff
                ? 'var(--status-verified-bg)'
                : 'var(--bg-surface-elevated)',
            border: `1px solid ${
              inventoryGap && Number(inventoryGap) > 0
                ? 'var(--status-urgent-border)'
                : isResolvedOrSignedOff
                ? 'var(--status-verified-border)'
                : 'var(--border-subtle)'
            }`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)' }}>
              {isResolvedOrSignedOff
                ? 'Incident Disposition Complete — Sign-off recorded'
                : inventoryGap && Number(inventoryGap) > 0
                ? `Operational Impact Identified: Potential Inventory Gap of ${inventoryGap} Days`
                : activeIncident?.entity_match_status === 'mismatch'
                ? 'Entity Mismatch Detected — Incident affects different company; escalation blocked'
                : policyRec === 'monitor'
                ? 'Low Operational Risk — Disruption duration covered by safety inventory'
                : 'Assessment in progress or requires supplier confirmation'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              {inventoryGap && Number(inventoryGap) > 0
                ? `Estimated disruption (${disruptionDays ?? '?'} days) exceeds safety stock coverage (${coverageDays ?? '?'} days) by ${inventoryGap} days.`
                : activeIncident?.policy_decision?.reasons?.[0] ||
                  'Evidence verified across reporting sources and evaluated against procurement policy.'}
            </div>
          </div>

          <div>
            {isReviewRequired ? (
              <span className="badge badge-urgent" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                Action Required: Human Review
              </span>
            ) : (
              <span className="badge badge-verified" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                Assessment Complete
              </span>
            )}
          </div>
        </div>

        {isRunLoading && (
          <div style={{ marginTop: '0.75rem', fontSize: '0.82rem', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>Retrieving web evidence, extracting quotes, and evaluating policy rules…</span>
          </div>
        )}
      </div>

      {/* ==================================================== */}
      {/* WORKSPACE GRID: EVIDENCE (LEFT) & IMPACT (RIGHT)     */}
      {/* ==================================================== */}
      <div className="investigation-grid">
        {/* -------------------------------------------------- */}
        {/* LEFT COLUMN: EVIDENCE, QUOTES & SOURCES            */}
        {/* -------------------------------------------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Section Navigation / Filter */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">
                <span>Supporting Evidence & Verbatim Quotes</span>
                <span className="badge badge-neutral">{claims.length} Claims</span>
              </span>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <button
                  className={`btn ${evidenceFilter === 'all' ? 'btn-secondary' : 'btn-outline'}`}
                  style={{ padding: '0.25rem 0.55rem', fontSize: '0.74rem' }}
                  onClick={() => setEvidenceFilter('all')}
                  type="button"
                >
                  All
                </button>
                <button
                  className={`btn ${evidenceFilter === 'claims' ? 'btn-secondary' : 'btn-outline'}`}
                  style={{ padding: '0.25rem 0.55rem', fontSize: '0.74rem' }}
                  onClick={() => setEvidenceFilter('claims')}
                  type="button"
                >
                  Quotes ({claims.length})
                </button>
                <button
                  className={`btn ${evidenceFilter === 'sources' ? 'btn-secondary' : 'btn-outline'}`}
                  style={{ padding: '0.25rem 0.55rem', fontSize: '0.74rem' }}
                  onClick={() => setEvidenceFilter('sources')}
                  type="button"
                >
                  Sources ({sources.length})
                </button>
              </div>
            </div>

            <div className="panel-body">
              {claims.length === 0 && !isRunLoading && (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem' }}>
                  No discrete claims extracted from retrieved sources.
                </p>
              )}

              {/* Claims & Quotes List */}
              {(evidenceFilter === 'all' || evidenceFilter === 'claims') && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {claims.map((claim) => {
                    const isQuoteVerified = claim.extraction_status === 'validated'
                    const sourceDoc = sources.find((s) => s.id === claim.source_id)

                    return (
                      <div
                        key={claim.id}
                        style={{
                          background: 'var(--bg-surface-elevated)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          padding: '1rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.4rem' }}>
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                              {claim.subject_text}
                            </div>
                            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                              Event: {claim.object_text}
                            </div>
                          </div>
                          <span className={`badge ${isQuoteVerified ? 'badge-verified' : 'badge-urgent'}`}>
                            {isQuoteVerified ? 'Exact Quote Verified' : 'Quote Mismatch'}
                          </span>
                        </div>

                        {/* Verbatim Supporting Quote */}
                        {claim.supporting_quote && (
                          <div className={`quote-card ${isQuoteVerified ? '' : 'mismatch'}`}>
                            "{claim.supporting_quote}"
                          </div>
                        )}

                        {/* Provenance Metadata */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                          <span>
                            Source: <strong style={{ color: 'var(--text-secondary)' }}>{sourceDoc?.publisher_name || sourceDoc?.domain || 'Unknown Publisher'}</strong>
                            {claim.event_date && ` • Event Date: ${claim.event_date}`}
                          </span>
                          {sourceDoc?.url_original && (
                            <a
                              href={sourceDoc.url_original}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                            >
                              <span>View Source</span>
                              <span>↗</span>
                            </a>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Source Documents List */}
              {(evidenceFilter === 'all' || evidenceFilter === 'sources') && sources.length > 0 && (
                <div style={{ marginTop: evidenceFilter === 'all' ? '1.5rem' : 0 }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem' }}>
                    Retrieved Source Documents ({sources.length})
                  </div>
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Publisher / Domain</th>
                          <th>Published</th>
                          <th>Status</th>
                          <th>Link</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sources.map((src) => (
                          <tr key={src.id}>
                            <td>
                              <strong style={{ color: 'var(--text-primary)' }}>
                                {src.publisher_name || src.domain}
                              </strong>
                            </td>
                            <td style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                              {src.published_at ? new Date(src.published_at).toLocaleDateString() : 'Unknown'}
                            </td>
                            <td>
                              <span
                                className={`badge ${
                                  src.content_status === 'available'
                                    ? 'badge-verified'
                                    : 'badge-caution'
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
                                style={{ fontSize: '0.78rem' }}
                              >
                                {src.domain || 'External Link'} ↗
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Source Lineage & Wire Deduplication */}
          {relations.length > 0 && (
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">
                  <span>Source Lineage & Wire Deduplication</span>
                  <span className="badge badge-caution">{relations.length} Relations Clustered</span>
                </span>
              </div>
              <div className="panel-body">
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  Syndicated news reprints sharing identical wire origin are clustered to prevent false corroboration.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                  {relations.map((rel) => (
                    <div
                      key={rel.id}
                      style={{
                        padding: '0.6rem 0.85rem',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.8rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>
                          {String((rel.evidence as Record<string, unknown>)?.observation || `Relation: ${rel.relation}`)}
                        </span>
                      </div>
                      <span className="badge badge-neutral">{rel.relation}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* -------------------------------------------------- */}
        {/* RIGHT COLUMN: IMPACT, POLICY & DECISION GATE       */}
        {/* -------------------------------------------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* 1. Operational Exposure Assessment */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Operational Impact Assessment</span>
              <span className="badge badge-neutral">Formula EX-003</span>
            </div>
            <div className="panel-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Estimated Disruption Duration:</span>
                  <strong style={{ color: 'var(--text-primary)' }}>
                    {disruptionDays !== undefined && disruptionDays !== null ? `${String(disruptionDays)} Days` : 'Not Specified'}
                  </strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Safety Inventory Coverage:</span>
                  <strong style={{ color: 'var(--text-primary)' }}>
                    {coverageDays !== undefined && coverageDays !== null ? `${String(coverageDays)} Days` : 'Not Specified'}
                  </strong>
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '0.65rem',
                    borderTop: '1px solid var(--border-subtle)',
                    marginTop: '0.25rem',
                  }}
                >
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.86rem' }}>
                    Potential Inventory Gap:
                  </span>
                  <span
                    className={`badge ${
                      inventoryGap && Number(inventoryGap) > 0 ? 'badge-urgent' : 'badge-verified'
                    }`}
                    style={{ fontSize: '0.9rem', fontWeight: 700 }}
                  >
                    {inventoryGap !== null && inventoryGap !== undefined ? `${inventoryGap} Days` : 'Unknown'}
                  </span>
                </div>

                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                  <em>Calculation:</em> Disruption ({disruptionDays != null ? String(disruptionDays) : '0'}d) − Inventory ({coverageDays != null ? String(coverageDays) : '0'}d) = {inventoryGap ? String(inventoryGap) : '0'}d gap.
                </div>
              </div>
            </div>
          </div>

          {/* 2. Policy Recommendation */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Policy Recommendation</span>
              <span className="badge badge-neutral">Procurement Policy</span>
            </div>
            <div className="panel-body">
              {activeIncident?.policy_decision ? (
                <div>
                  <div style={{ marginBottom: '0.75rem' }}>
                    <span
                      className={`badge ${
                        policyRec === 'urgent_human_review'
                          ? 'badge-urgent'
                          : policyRec === 'request_supplier_confirmation'
                          ? 'badge-caution'
                          : 'badge-info'
                      }`}
                      style={{ fontSize: '0.85rem', padding: '0.35rem 0.75rem', width: '100%', justifyContent: 'center' }}
                    >
                      {policyRec ? policyRec.replace(/_/g, ' ').toUpperCase() : 'UNKNOWN'}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {activeIncident.policy_decision.reasons?.map((reason, i) => (
                      <div key={i} style={{ display: 'flex', gap: '0.4rem' }}>
                        <span>•</span>
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>

                  {activeIncident.policy_decision.rule_ids_fired && (
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
                      Fired Policy Rule: {activeIncident.policy_decision.rule_ids_fired.join(', ')}
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>No policy evaluation recorded.</p>
              )}
            </div>
          </div>

          {/* 3. Human Decision Gate */}
          {activeIncident && (
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Human Decision Gate</span>
                <span className={`badge ${activeIncident.review_required ? 'badge-urgent' : 'badge-verified'}`}>
                  {activeIncident.review_required ? 'Sign-off Required' : 'Disposed'}
                </span>
              </div>
              <div className="panel-body">
                <form
                  onSubmit={(e) => {
                    e.preventDefault()
                    onSubmitDecision()
                  }}
                >
                  <div className="form-group">
                    <label className="form-label">Review Disposition:</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                      {[
                        { id: 'approve_recommendation', label: 'Accept Policy Recommendation' },
                        { id: 'request_more_information', label: 'Request Supplier Confirmation' },
                        { id: 'mark_monitor_only', label: 'Mark as Monitor Only' },
                        { id: 'reject_recommendation', label: 'Override / Reject Policy Action' },
                      ].map((act) => (
                        <label
                          key={act.id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            cursor: 'pointer',
                            fontSize: '0.82rem',
                            color: 'var(--text-primary)',
                          }}
                        >
                          <input
                            type="radio"
                            name="disposition"
                            value={act.id}
                            checked={decisionAction === act.id}
                            onChange={() => setDecisionAction(act.id as any)}
                          />
                          <span>{act.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {(decisionAction === 'reject_recommendation' || decisionAction === 'mark_monitor_only') && (
                    <div className="form-group">
                      <label className="form-label">Override Target Action:</label>
                      <select
                        className="form-select"
                        value={overrideRec}
                        onChange={(e) => setOverrideRec(e.target.value as any)}
                        required
                      >
                        <option value="">Select target action…</option>
                        <option value="monitor">Monitor Only</option>
                        <option value="request_supplier_confirmation">Request Supplier Confirmation</option>
                        <option value="review_contingency_plan">Review Contingency Plan</option>
                        <option value="urgent_human_review">Urgent Human Review</option>
                      </select>
                    </div>
                  )}

                  <div className="form-group">
                    <label className="form-label">Reviewer Name or Role:</label>
                    <input
                      type="text"
                      className="form-input"
                      value={reviewerName}
                      onChange={(e) => setReviewerName(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Audit Rationale:</label>
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
                        borderRadius: 'var(--radius-sm)',
                        background:
                          decisionFeedback.type === 'success'
                            ? 'var(--status-verified-bg)'
                            : 'var(--status-urgent-bg)',
                        color:
                          decisionFeedback.type === 'success'
                            ? 'var(--status-verified)'
                            : 'var(--status-urgent)',
                        fontSize: '0.8rem',
                        marginBottom: '0.75rem',
                        border: `1px solid ${
                          decisionFeedback.type === 'success'
                            ? 'var(--status-verified-border)'
                            : 'var(--status-urgent-border)'
                        }`,
                      }}
                    >
                      {decisionFeedback.msg}
                    </div>
                  )}

                  <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '0.6rem' }}
                    disabled={isReviewPending}
                  >
                    {isReviewPending ? 'Saving Decision…' : 'Record Decision & Sign Off'}
                  </button>
                </form>

                {reviews.length > 0 && (
                  <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                    <div style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                      Audit History ({reviews.length})
                    </div>
                    {reviews.map((rev) => (
                      <div key={rev.id} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                        <strong>{rev.reviewer_name}</strong>: {rev.action.replace(/_/g, ' ')} ({new Date(rev.reviewed_at).toLocaleDateString()})
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Collapsible Technical Details Trigger */}
          <div style={{ textAlign: 'center' }}>
            <button
              className="btn btn-outline"
              style={{ width: '100%', fontSize: '0.78rem' }}
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              type="button"
            >
              {showTechnicalDetails ? '▲ Hide Methodology Details' : '▼ View Methodology & Provenance Details'}
            </button>
          </div>

          {/* 4. Collapsible Methodology & Provenance Details */}
          {showTechnicalDetails && (
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Provenance & Evidence DAG</span>
                <span className="badge badge-neutral">Diagnostics</span>
              </div>
              <div className="panel-body">
                {(() => {
                  const provenance = (run?.metrics_json as Record<string, unknown>)?.provenance as
                    | {
                        quote_integrity_ratio?: number
                        source_independence_ratio?: number
                        data_completeness_score?: number
                        contradiction_count?: number
                      }
                    | undefined

                  if (!provenance) {
                    return <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No provenance metrics recorded.</p>
                  }

                  return (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
                      <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Completeness</div>
                        <strong>{Math.round((provenance.data_completeness_score ?? 1) * 100)}%</strong>
                      </div>
                      <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Quote Integrity</div>
                        <strong>{Math.round((provenance.quote_integrity_ratio ?? 1) * 100)}%</strong>
                      </div>
                      <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Independence</div>
                        <strong>{Math.round((provenance.source_independence_ratio ?? 1) * 100)}%</strong>
                      </div>
                      <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Contradictions</div>
                        <strong>{provenance.contradiction_count ?? 0}</strong>
                      </div>
                    </div>
                  )
                })()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
