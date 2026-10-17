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
  return (
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
        <button className="btn btn-primary" onClick={onNewInvestigation}>
          Start New Investigation
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Investigation Runs</span>
          <span className="pill pill-neutral">{investigations.length} Total Runs</span>
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
              {investigations.map((r) => {
                const sup = suppliers.find((s) => s.id === r.supplier_id)
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
                        onClick={() => onSelectRun(r)}
                      >
                        Open Workspace →
                      </button>
                    </td>
                  </tr>
                )
              })}
              {investigations.length === 0 && !isLoading && (
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
  )
}
