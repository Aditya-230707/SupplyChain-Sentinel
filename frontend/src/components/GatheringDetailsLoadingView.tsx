import { useState, useEffect } from 'react'

interface GatheringDetailsLoadingViewProps {
  supplierName: string
  country?: string | null
  partName?: string | null
  coverageDays?: string | null
  searchMode?: 'ddg' | 'live' | 'fixture' | string
  currentStatus?: string
  modelId?: string | null
}

const STAGES = [
  {
    id: 'search',
    title: '1. Ingesting Intelligence Sources',
    desc: 'Querying news wires, trade journals, and regulatory feeds with SSRF safety filters.',
  },
  {
    id: 'lineage',
    title: '2. Syndicated Wire Deduplication',
    desc: 'Clustering syndicated copies (Reuters, AP, Bloomberg) into singular reporting groups.',
  },
  {
    id: 'inference',
    title: '3. Nebius Token Factory Cloud Inference',
    desc: 'Executing NVIDIA Nemotron-3.5-Lightning with full neural reasoning for structured incident claims.',
  },
  {
    id: 'verification',
    title: '4. Deterministic Verification & Quote Grounding',
    desc: 'Rule E-005 exact substring character matching & Rule ID-001 multi-signal entity disambiguation.',
  },
  {
    id: 'exposure',
    title: '5. Operational Exposure & Policy Rulebook',
    desc: 'Evaluating Formula EX-003: balancing downtime recovery against safety stock coverage.',
  },
]

export function GatheringDetailsLoadingView({
  supplierName,
  country,
  partName,
  coverageDays,
  searchMode = 'ddg',
  currentStatus = 'searching',
  modelId = 'nvidia/Nemotron-3_5-Lightning',
}: GatheringDetailsLoadingViewProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Derive active stage based on currentStatus or elapsed seconds
  const getActiveStageIndex = () => {
    if (currentStatus === 'searching') return 0
    if (currentStatus === 'extracting') return 2
    if (currentStatus === 'resolving') return 3
    if (currentStatus === 'adjudicating' || currentStatus === 'assessing_impact') return 4
    if (currentStatus === 'completed') return 5

    // Fallback progression based on elapsed seconds if status is queued or pending
    if (elapsedSeconds < 3) return 0
    if (elapsedSeconds < 6) return 1
    if (elapsedSeconds < 14) return 2
    if (elapsedSeconds < 18) return 3
    return 4
  }

  const activeIndex = getActiveStageIndex()
  const progressPercent = Math.min(95, Math.round(((activeIndex + 0.6) / STAGES.length) * 100))

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '1rem 0 3rem 0' }}>
      {/* Top Banner */}
      <div
        className="panel"
        style={{
          background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--accent-subtle) 100%)',
          borderLeft: '4px solid var(--accent)',
          marginBottom: '1.25rem',
          padding: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1.25rem' }}>
            <img
              src="/logo.png"
              alt="Sentinel Logo"
              style={{ width: '56px', height: '56px', objectFit: 'contain', flexShrink: 0, marginTop: '4px' }}
            />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
                <span className="badge badge-urgent" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--status-urgent)',
                      animation: 'pulseGlow 1.4s infinite ease-in-out',
                    }}
                  />
                  Gathering Disruption Details
                </span>
                <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>
                  Mode: {searchMode === 'ddg' ? 'DuckDuckGo Live' : searchMode === 'live' ? 'Tavily News' : 'Simulated Fixture'}
                </span>
              </div>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Investigating {supplierName || 'Target Supplier'}
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginTop: '0.25rem' }}>
                Synthesizing public evidence, verifying verbatim quotations, and computing inventory gap exposure.
              </p>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Elapsed Time
            </div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>
              {formatTimer(elapsedSeconds)}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ marginTop: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
            <span>Pipeline Execution Progress</span>
            <span style={{ fontWeight: 600 }}>{progressPercent}%</span>
          </div>
          <div
            style={{
              height: '6px',
              backgroundColor: 'var(--border-base)',
              borderRadius: '3px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${progressPercent}%`,
                backgroundColor: 'var(--accent)',
                transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                background: 'linear-gradient(90deg, var(--accent) 0%, var(--border-focus) 100%)',
              }}
            />
          </div>
        </div>
      </div>

      {/* Target Investigation Profile Card */}
      <div className="panel" style={{ marginBottom: '1.25rem', padding: '1rem 1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Vendor Target
            </div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.2rem', fontSize: '0.88rem' }}>
              {supplierName || '—'}
            </div>
            {country && <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>{country}</div>}
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Component / Part
            </div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.2rem', fontSize: '0.88rem' }}>
              {partName || 'Automotive Microcontroller MCU-4'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Safety Inventory Buffer
            </div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.2rem', fontSize: '0.88rem' }}>
              {coverageDays ? `${coverageDays} Days Coverage` : '14 Days Default'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Neural Inference Engine
            </div>
            <div style={{ fontWeight: 600, color: 'var(--status-verified)', marginTop: '0.2rem', fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--status-verified)' }} />
              {modelId}
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Stepper */}
      <div className="panel" style={{ padding: '1.25rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
          Forensic Investigation Pipeline Stages
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {STAGES.map((stg, idx) => {
            const isFinished = activeIndex > idx
            const isCurrent = activeIndex === idx
            const isWaiting = activeIndex < idx

            return (
              <div
                key={stg.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.85rem',
                  padding: '0.75rem 0.9rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isCurrent ? 'var(--accent-subtle)' : isFinished ? 'var(--bg-surface)' : 'var(--bg-subtle)',
                  border: `1px solid ${isCurrent ? 'var(--accent-border)' : isFinished ? 'var(--status-verified-border)' : 'var(--border-subtle)'}`,
                  transition: 'all 0.3s ease',
                  opacity: isWaiting ? 0.65 : 1,
                }}
              >
                {/* Status Indicator Icon */}
                <div style={{ marginTop: '0.1rem' }}>
                  {isFinished ? (
                    <div
                      style={{
                        width: '22px',
                        height: '22px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--status-verified-bg)',
                        border: '1px solid var(--status-verified-border)',
                        color: 'var(--status-verified)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                      }}
                    >
                      ✓
                    </div>
                  ) : isCurrent ? (
                    <div
                      style={{
                        width: '22px',
                        height: '22px',
                        borderRadius: '50%',
                        border: '2px solid var(--accent)',
                        borderTopColor: 'transparent',
                        animation: 'spin 0.8s linear infinite',
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '22px',
                        height: '22px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-base)',
                        color: 'var(--text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.72rem',
                      }}
                    >
                      {idx + 1}
                    </div>
                  )}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span
                      style={{
                        fontWeight: isCurrent ? 700 : 600,
                        fontSize: '0.88rem',
                        color: isCurrent ? 'var(--accent)' : isFinished ? 'var(--status-verified)' : 'var(--text-secondary)',
                      }}
                    >
                      {stg.title}
                    </span>
                    {isCurrent && (
                      <span className="badge badge-caution" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>
                        Processing…
                      </span>
                    )}
                    {isFinished && (
                      <span className="badge badge-verified" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>
                        Verified
                      </span>
                    )}
                  </div>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    {stg.desc}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Explanatory Technical Note */}
      <div
        className="panel"
        style={{
          marginTop: '1.25rem',
          backgroundColor: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-base)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
        }}
      >
        <strong style={{ color: 'var(--text-primary)' }}>Why evidence gathering takes a few seconds:</strong>
        <div style={{ marginTop: '0.3rem' }}>
          Unlike generic chat wrappers that generate ungrounded opinions instantly, SupplyChain Sentinel executes exact substring character-index matching (Rule E-005) against full news articles, groups syndicated wires (Rules E-001–003) to prevent double-counting, and executes deep neural reasoning on Nebius Token Factory to eliminate hallucinations.
        </div>
      </div>
    </div>
  )
}
