import { useState } from 'react'
import type { InvestigationRun, SupplierListItem } from '../lib/api'

interface InvestigationsViewProps {
  investigations: InvestigationRun[]
  suppliers: SupplierListItem[]
  isLoading: boolean
  onSelectRun: (run: InvestigationRun) => void
  onNewInvestigation: () => void
}

export function InvestigationsView({
  investigations,
  suppliers,
  isLoading,
  onSelectRun,
  onNewInvestigation,
}: InvestigationsViewProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredRuns = investigations.filter((r) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    const sup = suppliers.find((s) => s.id === r.supplier_id)
    return (
      r.id.toLowerCase().includes(q) ||
      (sup && sup.name.toLowerCase().includes(q)) ||
      (sup?.country_or_region && sup.country_or_region.toLowerCase().includes(q))
    )
  })

  return (
    <div>
      {/* Page Title & Top Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 className="page-heading">
            Supplier Investigations
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginTop: '0.25rem' }}>
            Supplier incident investigations with verbatim quote verification and deterministic impact analysis.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input
            type="search"
            placeholder="Filter by supplier or run ID…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input"
            style={{ width: '240px', padding: '0.45rem 0.75rem', fontSize: '0.82rem' }}
          />
          <button className="btn btn-primary" onClick={onNewInvestigation} type="button">
            + Start Investigation
          </button>
        </div>
      </div>

      {/* Main Table Panel */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">
            <span>Recent Investigations</span>
            <span className="badge badge-neutral">{investigations.length}</span>
          </span>
          {isLoading && (
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Updating runs…
            </span>
          )}
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Supplier</th>
                <th>Run Identifier</th>
                <th>Discovery Mode</th>
                <th>Status</th>
                <th>Timestamp</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.map((run) => {
                const sup = suppliers.find((s) => s.id === run.supplier_id)
                const searchMode = (run.metrics_json as Record<string, unknown>)?.search_mode || 'fixture'

                return (
                  <tr key={run.id}>
                    <td>
                      <div>
                        <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                          {sup?.name || 'Unknown Supplier'}
                        </strong>
                        {sup?.country_or_region && (
                          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                            {sup.country_or_region}
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <code style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {run.id.slice(0, 8)}
                      </code>
                    </td>
                    <td>
                      {searchMode === 'ddg' ? (
                        <span className="badge badge-info">DuckDuckGo Live</span>
                      ) : searchMode === 'live' ? (
                        <span className="badge badge-verified">Tavily Live</span>
                      ) : (
                        <span className="badge badge-caution">Simulated Fixture</span>
                      )}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          run.status === 'completed'
                            ? 'badge-verified'
                            : run.status === 'failed'
                            ? 'badge-urgent'
                            : 'badge-info'
                        }`}
                      >
                        {run.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      {new Date(run.created_at).toLocaleString(undefined, {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.3rem 0.7rem', fontSize: '0.78rem' }}
                        onClick={() => onSelectRun(run)}
                        type="button"
                      >
                        Review Evidence →
                      </button>
                    </td>
                  </tr>
                )
              })}

              {filteredRuns.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-muted)' }}>
                    <div style={{ maxWidth: '360px', margin: '0 auto' }}>
                      <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem', opacity: 0.7 }}>🔍</div>
                      <p style={{ fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                        {searchQuery ? 'No matching investigations found' : 'No investigations recorded yet'}
                      </p>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                        {searchQuery
                          ? 'Try adjusting your search filter.'
                          : 'Run an investigation on a supplier to search public news sources and verify disruption claims.'}
                      </p>
                      {!searchQuery && (
                        <button className="btn btn-primary" onClick={onNewInvestigation} type="button">
                          Start First Investigation
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
