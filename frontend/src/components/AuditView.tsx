import { useState } from 'react'
import type { AuditEvent } from '../lib/api'

interface AuditViewProps {
  auditEvents: AuditEvent[]
}

export function AuditView({ auditEvents }: AuditViewProps) {
  const [filterQuery, setFilterQuery] = useState('')

  const filtered = auditEvents.filter((evt) => {
    if (!filterQuery.trim()) return true
    const q = filterQuery.toLowerCase()
    return (
      evt.event_type.toLowerCase().includes(q) ||
      (evt.entity_type && evt.entity_type.toLowerCase().includes(q)) ||
      JSON.stringify(evt.data).toLowerCase().includes(q)
    )
  })

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            Audit Trail
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginTop: '0.25rem' }}>
            Immutable record of recorded human review dispositions, overrides, and policy evaluations.
          </p>
        </div>
        <div>
          <input
            type="search"
            placeholder="Search audit records…"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="form-input"
            style={{ width: '240px', padding: '0.45rem 0.75rem', fontSize: '0.82rem' }}
          />
        </div>
      </div>

      {/* Main Panel */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">
            <span>Audit Events</span>
            <span className="badge badge-neutral">{auditEvents.length} Events Logged</span>
          </span>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '160px' }}>Timestamp</th>
                <th style={{ width: '150px' }}>Event Type</th>
                <th style={{ width: '120px' }}>Target Entity</th>
                <th>Audit Record Details</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((evt) => {
                const action = (evt.data as Record<string, unknown>)?.action
                const reviewer = (evt.data as Record<string, unknown>)?.reviewer_name
                const note = (evt.data as Record<string, unknown>)?.reviewer_note

                return (
                  <tr key={evt.id}>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                      {new Date(evt.created_at).toLocaleString(undefined, {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          evt.event_type.includes('decision') || evt.event_type.includes('human')
                            ? 'badge-verified'
                            : 'badge-neutral'
                        }`}
                      >
                        {evt.event_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                      {evt.entity_type || 'system'}
                    </td>
                    <td>
                      {action || reviewer ? (
                        <div style={{ fontSize: '0.82rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {String(action || 'Action Recorded').replace(/_/g, ' ')}
                          </span>
                          {Boolean(reviewer) && (
                            <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                              by {String(reviewer)}
                            </span>
                          )}
                          {Boolean(note) && (
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.76rem', marginTop: '0.2rem' }}>
                              Rationale: "{String(note)}"
                            </div>
                          )}
                        </div>
                      ) : (
                        <code style={{ fontSize: '0.76rem' }}>
                          {JSON.stringify(evt.data).slice(0, 120)}
                          {JSON.stringify(evt.data).length > 120 ? '…' : ''}
                        </code>
                      )}
                    </td>
                  </tr>
                )
              })}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                    {filterQuery ? 'No matching audit records.' : 'No audit records logged yet.'}
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
