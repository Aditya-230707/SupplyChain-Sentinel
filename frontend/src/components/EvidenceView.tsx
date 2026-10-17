import type { Claim, SourceDocument } from '../lib/api'

interface EvidenceViewProps {
  claims: Claim[]
  sources: SourceDocument[]
}

export function EvidenceView({ claims, sources }: EvidenceViewProps) {
  return (
    <div>
      <div style={{ marginBottom: '1.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          Deep Evidence Inspector
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
          Mathematical quote substring verification against stored immutable source documents (Rule E-005).
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Claims & Provenance Ledger</span>
          <span className="pill pill-neutral">{claims.length} Claims</span>
        </div>
        <div className="card-body">
          {claims.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
              No claims loaded. Open an investigation run from the Investigations list.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {claims.map((claim) => {
                const isVerified = claim.extraction_status === 'validated'
                const src = sources.find((s) => s.id === claim.source_id)

                return (
                  <div
                    key={claim.id}
                    style={{
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '1rem',
                      background: 'var(--surface-elevated)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ color: 'var(--text-primary)' }}>{claim.subject_text}</strong>
                      <span className={`pill ${isVerified ? 'pill-success' : 'pill-danger'}`}>
                        {isVerified ? 'VERIFIED EXACT (Rule E-005)' : 'QUOTE MISMATCH'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      Claimed Event: {claim.object_text}
                    </div>
                    <div className={`quote-box ${isVerified ? 'quote-verified' : 'quote-mismatch'}`} style={{ margin: '0.5rem 0' }}>
                      "{claim.supporting_quote}"
                    </div>
                    {src && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Publisher: {src.publisher_name || src.domain}</span>
                        <a href={src.url_original} target="_blank" rel="noopener noreferrer">
                          {src.url_original.slice(0, 50)}… ↗
                        </a>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
