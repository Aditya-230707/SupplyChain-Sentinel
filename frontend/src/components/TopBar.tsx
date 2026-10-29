import type { ActiveTab } from '../lib/constants'

interface TopBarProps {
  activeTab: ActiveTab
  activeRunId: string | null
  activeSupplierName?: string | null
  searchMode: 'ddg' | 'live' | 'fixture'
  onNavigateTab: (tab: ActiveTab) => void
  onNewInvestigation: () => void
}

export function TopBar({
  activeTab,
  activeRunId,
  activeSupplierName,
  searchMode,
  onNavigateTab,
  onNewInvestigation,
}: TopBarProps) {
  return (
    <header className="top-bar">
      <div className="breadcrumbs" style={{ display: 'flex', alignItems: 'center' }}>
        <img
          src="/logo.png"
          alt="Sentinel Logo"
          style={{ width: '22px', height: '22px', objectFit: 'contain', marginRight: '6px' }}
        />
        <span>Sentinel</span>
        <span style={{ marginLeft: '4px' }}>/</span>

        {activeTab === 'investigations' && (
          <span className="breadcrumb-current">Investigations</span>
        )}

        {activeTab === 'new_investigation' && (
          <>
            <button
              onClick={() => onNavigateTab('investigations')}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
            >
              Investigations
            </button>
            <span>/</span>
            <span className="breadcrumb-current">New Investigation</span>
          </>
        )}

        {activeTab === 'workspace' && (
          <>
            <button
              onClick={() => onNavigateTab('investigations')}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}
            >
              Investigations
            </button>
            <span>/</span>
            <span className="breadcrumb-current">
              {activeSupplierName || (activeRunId ? `Run ${activeRunId.slice(0, 8)}` : 'Active Investigation')}
            </span>
          </>
        )}

        {activeTab === 'suppliers' && (
          <span className="breadcrumb-current">Suppliers</span>
        )}

        {activeTab === 'audit' && (
          <span className="breadcrumb-current">Audit Trail</span>
        )}
      </div>

      <div className="topbar-actions">
        {activeTab === 'workspace' && (
          <button
            className="btn btn-outline"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            onClick={() => onNavigateTab('investigations')}
            type="button"
          >
            ← Back to Investigations
          </button>
        )}

        <span className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>
          Mode: {searchMode === 'ddg' ? 'DuckDuckGo Live' : searchMode === 'live' ? 'Tavily Live' : 'Simulated Fixture'}
        </span>

        {activeTab !== 'new_investigation' && (
          <button
            className="btn btn-primary"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            onClick={onNewInvestigation}
            type="button"
          >
            + New Investigation
          </button>
        )}
      </div>
    </header>
  )
}
