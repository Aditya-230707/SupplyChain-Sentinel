import type { AppHealth, ProvidersHealthResponse } from '../lib/api'

interface DiagnosticsModalProps {
  isOpen: boolean
  onClose: () => void
  health?: AppHealth
  providersHealth?: ProvidersHealthResponse
}

export function DiagnosticsModal({
  isOpen,
  onClose,
  health,
  providersHealth,
}: DiagnosticsModalProps) {
  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        className="panel"
        style={{
          width: '100%',
          maxWidth: '560px',
          margin: 0,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-header">
          <span className="panel-title">System Diagnostics</span>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.1rem',
              cursor: 'pointer',
              padding: '0.2rem 0.4rem',
            }}
            type="button"
          >
            ✕
          </button>
        </div>

        <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* LLM Inference */}
          <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>LLM Inference Engine</strong>
              <span className="badge badge-verified">Configured</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              <div>Provider: <code>{providersHealth?.llm?.provider_name || 'ollama'}</code></div>
              <div>Model ID: <code>{providersHealth?.llm?.model_id || 'qwen3.5:9b'}</code></div>
              <div>Status: {providersHealth?.llm?.reachable !== false ? 'Online & responsive' : 'Unreachable'}</div>
            </div>
          </div>

          {/* Web Search */}
          <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>Web Search & Retrieval</strong>
              <span className="badge badge-verified">Active</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              <div>
                Primary Provider:{' '}
                <code>{providersHealth?.search?.provider_name === 'tavily_search' ? 'Tavily Search' : 'DuckDuckGo Live Search'}</code>
              </div>
              <div>Guardrails: Max 6 queries per investigation, sanitized via BeautifulSoup</div>
            </div>
          </div>

          {/* Application & DB */}
          <div style={{ background: 'var(--bg-surface-elevated)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>Application & Database</strong>
              <span className="badge badge-verified">{health?.status ? health.status.toUpperCase() : 'OK'}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              <div>Version: {health?.version || '0.1.0'} ({health?.environment || 'development'})</div>
              <div>Persistence: SQLite async (SQLAlchemy)</div>
              <div>Heartbeat: {health?.timestamp || 'Normal'}</div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button className="btn btn-secondary" onClick={onClose} type="button">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
