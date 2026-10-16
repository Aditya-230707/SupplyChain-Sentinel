import { useQuery } from '@tanstack/react-query'
import { getHealth } from './lib/api'

function StatusBadge({ ok }: { ok: boolean }) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '0.8em',
        fontWeight: 600,
        background: ok ? '#d4edda' : '#f8d7da',
        color: ok ? '#155724' : '#721c24',
      }}
    >
      {ok ? 'OK' : 'ERROR'}
    </span>
  )
}

export default function App() {
  const { data: health, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30_000,
  })

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Header */}
      <header style={{ marginBottom: '2rem', borderBottom: '2px solid #dee2e6', paddingBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1a1a2e' }}>
          🛡️ SupplyChain Sentinel
        </h1>
        <p style={{ color: '#6c757d', marginTop: '0.25rem' }}>
          Evidence-first supplier incident intelligence
        </p>
      </header>

      {/* Health Status */}
      <section aria-label="System status" style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          System Status
        </h2>

        {isLoading && <p style={{ color: '#6c757d' }}>Checking backend…</p>}
        {isError && (
          <div
            role="alert"
            style={{
              padding: '0.75rem 1rem',
              background: '#f8d7da',
              border: '1px solid #f5c6cb',
              borderRadius: '6px',
              color: '#721c24',
            }}
          >
            Cannot reach backend. Make sure <code>uvicorn app.main:app --port 8000</code> is running.
          </div>
        )}

        {health && (
          <table style={{ borderCollapse: 'collapse', width: '100%', maxWidth: 500 }}>
            <tbody>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', color: '#495057' }}>API</td>
                <td><StatusBadge ok={health.status === 'ok'} /></td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', color: '#495057' }}>Database</td>
                <td><StatusBadge ok={health.database.ok} /></td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', color: '#495057' }}>Environment</td>
                <td><code>{health.environment}</code></td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', color: '#495057' }}>Version</td>
                <td><code>{health.version}</code></td>
              </tr>
            </tbody>
          </table>
        )}
      </section>

      {/* Phase notice */}
      <section
        style={{
          padding: '1rem',
          background: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '6px',
          marginBottom: '2rem',
        }}
      >
        <strong>Phase 1 — Bootstrap</strong>
        <p style={{ marginTop: '0.4rem', color: '#856404' }}>
          Core infrastructure is running. Supplier management, investigation pipeline, and
          review UI will be built in Phases 2–4.
        </p>
      </section>

      {/* Key principles — transparency */}
      <section>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Design Principles
        </h2>
        <ul style={{ paddingLeft: '1.25rem', color: '#495057', lineHeight: 1.8 }}>
          <li>Every factual statement links to a stored evidence record</li>
          <li>Deterministic code — not AI — calculates inventory gaps and enforces policy rules</li>
          <li>Unknown values stay <strong>unknown</strong>, never zero</li>
          <li>No autonomous supplier suspensions — all consequential actions require human review</li>
          <li>Model-produced confidence values are <em>not</em> calibrated probabilities</li>
        </ul>
      </section>
    </div>
  )
}
