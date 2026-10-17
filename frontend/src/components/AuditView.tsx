import type { AuditEvent } from '../lib/api'

interface AuditViewProps {
  auditEvents: AuditEvent[]
}

export function AuditView({ auditEvents }: AuditViewProps) {
  return (
    <div>
      <div style={{ marginBottom: '1.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          Immutable Audit Ledger
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
          Cryptographically structured audit trail recording all human dispositions, overrides, and policy evaluations.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Event Ledger</span>
          <span className="pill pill-neutral">{auditEvents.length} Events</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Entity</th>
                <th>Event Details</th>
              </tr>
            </thead>
            <tbody>
              {auditEvents.map((evt) => (
                <tr key={evt.id}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {new Date(evt.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span className="pill pill-info">{evt.event_type}</span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{evt.entity_type}</td>
                  <td>
                    <code style={{ fontSize: '0.76rem' }}>
                      {JSON.stringify(evt.data).slice(0, 110)}
                      {JSON.stringify(evt.data).length > 110 ? '…' : ''}
                    </code>
                  </td>
                </tr>
              ))}
              {auditEvents.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No audit events logged yet.
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
