import type { ActiveTab } from '../lib/constants'

interface TopBarProps {
  activeTab: ActiveTab
  activeRunId: string | null
  searchMode: 'ddg' | 'live' | 'fixture'
  onNewInvestigation: () => void
}

export function TopBar({
  activeTab,
  activeRunId,
  searchMode,
  onNewInvestigation,
}: TopBarProps) {
  return (
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
            onClick={onNewInvestigation}
          >
            + New Investigation
          </button>
        )}
      </div>
    </header>
  )
}
