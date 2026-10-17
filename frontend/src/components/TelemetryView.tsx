import type { AppHealth, ProvidersHealthResponse } from '../lib/api'

interface TelemetryViewProps {
  health?: AppHealth
  providersHealth?: ProvidersHealthResponse
  isTavilyAvailable: boolean
}

export function TelemetryView({
  health,
  providersHealth,
  isTavilyAvailable,
}: TelemetryViewProps) {
  return (
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
            <div>
              <strong>Provider:</strong> <code>{providersHealth?.llm?.provider_name || 'ollama'}</code>
            </div>
            <div>
              <strong>Active Model:</strong> <code>{providersHealth?.llm?.model_id || 'qwen3.5:9b'}</code>
            </div>
            <div>
              <strong>Endpoint:</strong> <code>http://localhost:11434</code>
            </div>
            <div>
              <strong>Architecture:</strong> Local Ollama on CPU / CUDA
            </div>
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
            {health?.status ? health.status.toUpperCase() : 'UNKNOWN'}
          </span>
        </div>
        <div className="card-body">
          <div style={{ fontSize: '0.86rem', lineHeight: 2 }}>
            <div>
              <strong>Version:</strong> {health?.version || '0.1.0'}
            </div>
            <div>
              <strong>Environment:</strong> {health?.environment || 'development'}
            </div>
            <div>
              <strong>Database Status:</strong>{' '}
              {health?.database?.ok ? 'Connected (SQLite async)' : 'Degraded'}
            </div>
            <div>
              <strong>Last Heartbeat:</strong> {health?.timestamp || 'Just now'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
