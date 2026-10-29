import type { ProvidersHealthResponse } from '../lib/api'
import type { ActiveTab } from '../lib/constants'

interface SidebarProps {
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void
  investigationsCount: number
  suppliersCount: number
  auditCount: number
  activeRunId: string | null
  hasReviewRequired: boolean
  providersHealth?: ProvidersHealthResponse
  onNewInvestigation: () => void
  onOpenDiagnostics: () => void
}

export function Sidebar({
  activeTab,
  setActiveTab,
  investigationsCount,
  suppliersCount,
  auditCount,
  activeRunId,
  hasReviewRequired,
  providersHealth,
  onNewInvestigation,
  onOpenDiagnostics,
}: SidebarProps) {
  const isViewingWorkspace = activeTab === 'workspace' && activeRunId

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <img
            src="/logo.png"
            alt="Sentinel Logo"
            className="sidebar-brand-img"
            style={{ width: '28px', height: '28px', objectFit: 'contain' }}
          />
          <span>SupplyChain Sentinel</span>
        </div>
      </div>

      <div className="sidebar-body">
        {/* Primary Call to Action */}
        <div>
          <button
            className="sidebar-primary-btn"
            onClick={onNewInvestigation}
            type="button"
          >
            <span>+</span>
            <span>New Investigation</span>
          </button>
        </div>

        {/* Primary Navigation */}
        <div>
          <div className="nav-section-label">Workspace</div>
          <nav className="nav-list" aria-label="Main navigation">
            <button
              className={`nav-item ${activeTab === 'investigations' ? 'active' : ''}`}
              onClick={() => setActiveTab('investigations')}
              type="button"
            >
              <span>Investigations</span>
              <span className="nav-badge">{investigationsCount}</span>
            </button>

            {isViewingWorkspace && (
              <button
                className={`nav-item ${activeTab === 'workspace' ? 'active' : ''}`}
                onClick={() => setActiveTab('workspace')}
                style={{ paddingLeft: '1.25rem' }}
                type="button"
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>↳</span>
                  <span>Active Run</span>
                </span>
                {hasReviewRequired ? (
                  <span className="badge badge-urgent" style={{ fontSize: '0.68rem', padding: '0.1rem 0.35rem' }}>
                    Review
                  </span>
                ) : (
                  <span className="nav-badge">{activeRunId.slice(0, 6)}</span>
                )}
              </button>
            )}

            <button
              className={`nav-item ${activeTab === 'suppliers' ? 'active' : ''}`}
              onClick={() => setActiveTab('suppliers')}
              type="button"
            >
              <span>Suppliers</span>
              <span className="nav-badge">{suppliersCount}</span>
            </button>

            <button
              className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
              onClick={() => setActiveTab('audit')}
              type="button"
            >
              <span>Audit Trail</span>
              <span className="nav-badge">{auditCount}</span>
            </button>

            <button
              className={`nav-item ${activeTab === 'manual' ? 'active' : ''}`}
              onClick={() => setActiveTab('manual')}
              type="button"
            >
              <span>User Manual</span>
              <span className="nav-badge" style={{ backgroundColor: 'var(--status-verified-bg)', color: 'var(--status-verified)', borderColor: 'var(--status-verified-border)' }}>Guide</span>
            </button>
          </nav>
        </div>
      </div>

      {/* System Status Footer */}
      <div className="sidebar-footer">
        <div className="status-row">
          <span>Inference</span>
          <span className="status-pill-indicator">
            <span className="status-dot" />
            <span>{providersHealth?.llm?.model_id || 'nvidia/Nemotron-3_5-Lightning'}</span>
          </span>
        </div>
        <div className="status-row">
          <span>Search</span>
          <span style={{ color: 'var(--text-secondary)' }}>
            {providersHealth?.search?.provider_name === 'tavily_search' ? 'Tavily' : 'DuckDuckGo Live'}
          </span>
        </div>
        <div style={{ marginTop: '0.35rem', paddingTop: '0.35rem', borderTop: '1px solid var(--border-subtle)' }}>
          <button
            onClick={onOpenDiagnostics}
            className="btn btn-outline"
            style={{ width: '100%', padding: '0.3rem 0.5rem', fontSize: '0.74rem', justifyContent: 'center' }}
            type="button"
          >
            System Diagnostics
          </button>
        </div>
      </div>
    </aside>
  )
}
