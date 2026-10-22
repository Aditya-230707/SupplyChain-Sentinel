import { useState } from 'react'
import type { SupplierListItem } from '../lib/api'
import { BENCHMARK_SCENARIOS } from '../lib/constants'

interface NewInvestigationViewProps {
  searchMode: 'ddg' | 'live' | 'fixture'
  setSearchMode: (mode: 'ddg' | 'live' | 'fixture') => void
  suppliers: SupplierListItem[]
  isTavilyAvailable: boolean
  onSubmit: (params: {
    mode: 'ddg' | 'live' | 'fixture'
    supplierMode: 'existing' | 'new'
    existingSupplierId?: string
    name?: string
    country?: string
    domain?: string
    criticality: 'low' | 'medium' | 'high' | 'unknown'
    partName?: string
    coverage?: string
    recovery?: string
    categories: string[]
  }) => void
  onCancel: () => void
  isPending: boolean
}

export function NewInvestigationView({
  searchMode,
  setSearchMode,
  suppliers,
  isTavilyAvailable,
  onSubmit,
  onCancel,
  isPending,
}: NewInvestigationViewProps) {
  const [formSupplierMode, setFormSupplierMode] = useState<'existing' | 'new'>('new')
  const [formExistingSupplierId, setFormExistingSupplierId] = useState<string>('')
  const [formName, setFormName] = useState<string>('')
  const [formCountry, setFormCountry] = useState<string>('')
  const [formDomain, setFormDomain] = useState<string>('')
  const [formCriticality, setFormCriticality] = useState<'low' | 'medium' | 'high' | 'unknown'>('high')
  const [formPartName, setFormPartName] = useState<string>('')
  const [formCoverageDays, setFormCoverageDays] = useState<string>('')
  const [formRecoveryDays, setFormRecoveryDays] = useState<string>('')
  const [formCategories, setFormCategories] = useState<string[]>([
    'operational_disruption',
    'environmental_regulatory',
    'logistics_disruption',
  ])

  const handlePreFillScenario = (key: string) => {
    const sc = BENCHMARK_SCENARIOS.find((s) => s.key === key)
    if (!sc) return
    setFormSupplierMode('new')
    setFormName(sc.supplierName)
    setFormCountry(sc.country)
    setFormDomain(sc.domain)
    setFormCriticality(sc.criticality)
    setFormPartName(sc.partName)
    setFormCoverageDays(sc.coverage)
    setFormRecoveryDays(sc.recovery || '')
    setSearchMode('fixture')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      mode: searchMode,
      supplierMode: formSupplierMode,
      existingSupplierId: formExistingSupplierId,
      name: formName,
      country: formCountry,
      domain: formDomain,
      criticality: formCriticality,
      partName: formPartName,
      coverage: formCoverageDays,
      recovery: formRecoveryDays,
      categories: formCategories,
    })
  }

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto' }}>
      {/* Title */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            New Supplier Investigation
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginTop: '0.25rem' }}>
            Search public sources for incident reports, verify quotes, and evaluate inventory exposure.
          </p>
        </div>

        {/* Quick Pre-fill Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Sample Scenario:</span>
          <select
            className="form-select"
            style={{ width: 'auto', padding: '0.35rem 1.8rem 0.35rem 0.65rem', fontSize: '0.78rem' }}
            onChange={(e) => e.target.value && handlePreFillScenario(e.target.value)}
            defaultValue=""
          >
            <option value="" disabled>
              Select scenario to pre-fill…
            </option>
            {BENCHMARK_SCENARIOS.map((sc) => (
              <option key={sc.key} value={sc.key}>
                {sc.title} ({sc.supplierName})
              </option>
            ))}
          </select>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Discovery Mode Selection */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">1. Search & Discovery Engine</span>
          </div>
          <div className="panel-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.85rem' }}>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.65rem',
                  padding: '0.85rem',
                  border: `1px solid ${searchMode === 'ddg' ? 'var(--accent)' : 'var(--border-base)'}`,
                  borderRadius: 'var(--radius-md)',
                  background: searchMode === 'ddg' ? 'var(--accent-subtle)' : 'var(--bg-surface-elevated)',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="radio"
                  name="searchModeRadio"
                  value="ddg"
                  checked={searchMode === 'ddg'}
                  onChange={() => setSearchMode('ddg')}
                  style={{ marginTop: '0.2rem' }}
                />
                <div>
                  <strong style={{ color: 'var(--text-primary)', fontSize: '0.86rem' }}>DuckDuckGo Live</strong>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    Searches live public web and news without requiring third-party API keys.
                  </div>
                </div>
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.65rem',
                  padding: '0.85rem',
                  border: `1px solid ${searchMode === 'fixture' ? 'var(--status-caution)' : 'var(--border-base)'}`,
                  borderRadius: 'var(--radius-md)',
                  background: searchMode === 'fixture' ? 'var(--status-caution-bg)' : 'var(--bg-surface-elevated)',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="radio"
                  name="searchModeRadio"
                  value="fixture"
                  checked={searchMode === 'fixture'}
                  onChange={() => setSearchMode('fixture')}
                  style={{ marginTop: '0.2rem' }}
                />
                <div>
                  <strong style={{ color: 'var(--text-primary)', fontSize: '0.86rem' }}>Deterministic Fixtures</strong>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    Reproducible local test scenarios for evaluation and offline validation.
                  </div>
                </div>
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.65rem',
                  padding: '0.85rem',
                  border: `1px solid ${searchMode === 'live' ? 'var(--accent)' : 'var(--border-base)'}`,
                  borderRadius: 'var(--radius-md)',
                  background: searchMode === 'live' ? 'var(--accent-subtle)' : 'var(--bg-surface-elevated)',
                  cursor: isTavilyAvailable ? 'pointer' : 'not-allowed',
                  opacity: isTavilyAvailable ? 1 : 0.5,
                }}
              >
                <input
                  type="radio"
                  name="searchModeRadio"
                  value="live"
                  checked={searchMode === 'live'}
                  onChange={() => isTavilyAvailable && setSearchMode('live')}
                  disabled={!isTavilyAvailable}
                  style={{ marginTop: '0.2rem' }}
                />
                <div>
                  <strong style={{ color: 'var(--text-primary)', fontSize: '0.86rem' }}>Tavily Search</strong>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    {isTavilyAvailable ? 'Tavily cloud indexing enabled.' : 'Requires TAVILY_API_KEY in .env.'}
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Step 2: Supplier Target Profile */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">2. Target Supplier</span>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <button
                type="button"
                className={`btn ${formSupplierMode === 'new' ? 'btn-secondary' : 'btn-outline'}`}
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.76rem' }}
                onClick={() => setFormSupplierMode('new')}
              >
                Enter Details
              </button>
              <button
                type="button"
                className={`btn ${formSupplierMode === 'existing' ? 'btn-secondary' : 'btn-outline'}`}
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.76rem' }}
                onClick={() => setFormSupplierMode('existing')}
              >
                Select Existing ({suppliers.length})
              </button>
            </div>
          </div>

          <div className="panel-body">
            {formSupplierMode === 'existing' ? (
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Select Registered Supplier:</label>
                <select
                  className="form-select"
                  value={formExistingSupplierId}
                  onChange={(e) => setFormExistingSupplierId(e.target.value)}
                  required
                >
                  <option value="">Choose a registered supplier…</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.country_or_region || 'Unknown Region'}) — {s.criticality} criticality
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="grid-2">
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Supplier Legal Name *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Silicon Foundry Dresden GmbH"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Country / Jurisdiction</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Germany"
                      value={formCountry}
                      onChange={(e) => setFormCountry(e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid-2">
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Official Domain (for entity resolution)</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. silicon-dresden.de"
                      value={formDomain}
                      onChange={(e) => setFormDomain(e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Criticality Tier</label>
                    <select
                      className="form-select"
                      value={formCriticality}
                      onChange={(e) => setFormCriticality(e.target.value as any)}
                    >
                      <option value="high">High Criticality (Tier 1)</option>
                      <option value="medium">Medium Criticality (Tier 2)</option>
                      <option value="low">Low Criticality (Tier 3)</option>
                      <option value="unknown">Unknown</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Step 3: Operational Stock Buffer (Optional) */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">3. Operational Exposure Context (Optional)</span>
            <span className="badge badge-neutral">Formula EX-003</span>
          </div>
          <div className="panel-body">
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Used to calculate potential inventory gap: <code>Gap = max(0, Disruption Duration − Safety Stock)</code>.
            </p>
            <div className="grid-3">
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Critical Component / Part Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Automotive Microcontroller MCU-4"
                  value={formPartName}
                  onChange={(e) => setFormPartName(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Safety Stock Coverage (Days)</label>
                <input
                  type="number"
                  min="0"
                  className="form-input"
                  placeholder="e.g. 14"
                  value={formCoverageDays}
                  onChange={(e) => setFormCoverageDays(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Estimated Disruption (Days)</label>
                <input
                  type="number"
                  min="0"
                  className="form-input"
                  placeholder="e.g. 45"
                  value={formRecoveryDays}
                  onChange={(e) => setFormRecoveryDays(e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Step 4: Incident Categories */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">4. Incident Categories to Monitor</span>
          </div>
          <div className="panel-body">
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
              {[
                { id: 'operational_disruption', label: 'Operational Disruption (Fire, Power, Outage)' },
                { id: 'environmental_regulatory', label: 'Environmental & Regulatory (Sanctions, EPA)' },
                { id: 'logistics_disruption', label: 'Logistics Disruption (Ports, Rail, Freight)' },
              ].map((cat) => (
                <label
                  key={cat.id}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.84rem' }}
                >
                  <input
                    type="checkbox"
                    checked={formCategories.includes(cat.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormCategories([...formCategories, cat.id])
                      } else {
                        setFormCategories(formCategories.filter((c) => c !== cat.id))
                      }
                    }}
                  />
                  <span style={{ color: 'var(--text-primary)' }}>{cat.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
          <button type="button" className="btn btn-outline" onClick={onCancel} disabled={isPending}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ padding: '0.6rem 1.5rem', fontSize: '0.88rem' }}
            disabled={isPending}
          >
            {isPending ? 'Starting Investigation…' : 'Start Investigation →'}
          </button>
        </div>
      </form>
    </div>
  )
}
