import { useState } from 'react'
import type { ProvidersHealthResponse } from '../lib/api'
import { BENCHMARK_SCENARIOS, type ActiveTab, type BenchmarkScenario } from '../lib/constants'

interface SidebarProps {
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void
  investigationsCount: number
  suppliersCount: number
  claimsCount: number
  auditCount: number
  activeRunId: string | null
  hasReviewRequired: boolean
  providersHealth?: ProvidersHealthResponse
  onLaunchBenchmark: (scenario: BenchmarkScenario) => void
  isLaunching: boolean
}

export function Sidebar({
  activeTab,
  setActiveTab,
  investigationsCount,
  suppliersCount,
  claimsCount,
  auditCount,
  activeRunId,
  hasReviewRequired,
  providersHealth,
  onLaunchBenchmark,
  isLaunching,
}: SidebarProps) {
  const [showBenchmarkDrawer, setShowBenchmarkDrawer] = useState(false)

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand-sys">Core // Node 01</div>
        <div className="sidebar-brand-title">SENTINEL</div>
        <div className="sidebar-brand-subtitle">Industrial Intelligence</div>
      </div>

      <div className="sidebar-content">
        <div>
          <div className="sidebar-section-title">Navigation</div>
          <div className="sidebar-nav-list">
            <button
              className={`sidebar-nav-item ${activeTab === 'investigations' ? 'active' : ''}`}
              onClick={() => setActiveTab('investigations')}
            >
              <span>Investigations</span>
              <span className="nav-count">{investigationsCount}</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'new_investigation' ? 'active' : ''}`}
              onClick={() => setActiveTab('new_investigation')}
            >
              <span>+ New Investigation</span>
              <span className="nav-count" style={{ color: 'var(--accent)' }}>LIVE</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'workspace' ? 'active' : ''}`}
              onClick={() => setActiveTab('workspace')}
            >
              <span>Active Workspace</span>
              {activeRunId && (
                <span className="nav-count" style={{ color: 'var(--accent)' }}>
                  {activeRunId.slice(0, 6)}
                </span>
              )}
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'suppliers' ? 'active' : ''}`}
              onClick={() => setActiveTab('suppliers')}
            >
              <span>Supplier Registry</span>
              <span className="nav-count">{suppliersCount}</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'evidence' ? 'active' : ''}`}
              onClick={() => setActiveTab('evidence')}
            >
              <span>Evidence & Quotes</span>
              <span className="nav-count">{claimsCount}</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'decision' ? 'active' : ''}`}
              onClick={() => setActiveTab('decision')}
            >
              <span>Human Decision Gate</span>
              {hasReviewRequired && (
                <span className="nav-count" style={{ background: 'rgba(255, 90, 90, 0.2)', color: 'var(--error)' }}>
                  REQ
                </span>
              )}
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'audit' ? 'active' : ''}`}
              onClick={() => setActiveTab('audit')}
            >
              <span>Audit Ledger</span>
              <span className="nav-count">{auditCount}</span>
            </button>

            <button
              className={`sidebar-nav-item ${activeTab === 'telemetry' ? 'active' : ''}`}
              onClick={() => setActiveTab('telemetry')}
            >
              <span>System Telemetry</span>
              <span className="nav-count">DIAG</span>
            </button>
          </div>
        </div>

        {/* Benchmark Scenarios (Simulated Fixtures) Drawer */}
        <div>
          <div
            className="sidebar-section-title"
            style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer', alignItems: 'center' }}
            onClick={() => setShowBenchmarkDrawer(!showBenchmarkDrawer)}
          >
            <span>Benchmark Suites</span>
            <span style={{ fontSize: '0.7rem' }}>{showBenchmarkDrawer ? '▲' : '▼'}</span>
          </div>

          {showBenchmarkDrawer && (
            <div className="sidebar-benchmarks-box">
              <div className="benchmark-tag">Simulated Fixtures</div>
              <div className="benchmark-desc">
                Deterministic synthetic scenarios for policy regression tests and offline validation.
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {BENCHMARK_SCENARIOS.map((sc) => (
                  <button
                    key={sc.key}
                    className="btn btn-outline"
                    style={{
                      padding: '0.4rem 0.6rem',
                      fontSize: '0.74rem',
                      textAlign: 'left',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.15rem',
                    }}
                    onClick={() => onLaunchBenchmark(sc)}
                    disabled={isLaunching}
                  >
                    <strong style={{ color: 'var(--text-primary)' }}>{sc.title}</strong>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>{sc.supplierName}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Status Footer */}
      <div className="sidebar-footer">
        <div className="engine-status-row">
          <span>LLM ENGINE</span>
          <span className="engine-status-val online">
            {providersHealth?.llm?.model_id || 'qwen3.5:9b'}
          </span>
        </div>
        <div className="engine-status-row">
          <span>WEB SEARCH</span>
          <span className="engine-status-val online">
            {providersHealth?.search?.provider_name === 'tavily_search' ? 'TAVILY' : 'DUCKDUCKGO'}
          </span>
        </div>
        <div className="engine-status-row">
          <span>ENVIRONMENT</span>
          <span style={{ color: 'var(--text-secondary)' }}>LOCAL DEV</span>
        </div>
      </div>
    </aside>
  )
}
