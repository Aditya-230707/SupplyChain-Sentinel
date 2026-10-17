import { useState } from 'react'
import type { SupplierListItem } from '../lib/api'

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
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          Initiate Supplier Incident Investigation
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.86rem', marginTop: '0.2rem' }}>
          Execute real-time public discovery, local Ollama claim extraction, and deterministic policy rulebook evaluation.
        </p>
      </div>

      {/* Mode Control Card */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div className="card-header">
          <span className="card-title">Search & Discovery Engine</span>
          <span className="pill pill-info">Source Provider Selection</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.65rem',
                padding: '0.85rem',
                border: `1px solid ${searchMode === 'ddg' ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-sm)',
                background: searchMode === 'ddg' ? 'rgba(0, 217, 255, 0.05)' : 'var(--surface-elevated)',
                cursor: 'pointer',
              }}
            >
              <input
                type="radio"
                name="modeChoice"
                value="ddg"
                checked={searchMode === 'ddg'}
                onChange={() => setSearchMode('ddg')}
                style={{ marginTop: '0.25rem' }}
              />
              <div>
                <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>DuckDuckGo Live Search</strong>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Primary live engine. Discovers live public news & articles without external API keys.
                </div>
              </div>
            </label>

            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.65rem',
                padding: '0.85rem',
                border: `1px solid ${searchMode === 'live' ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-sm)',
                background: searchMode === 'live' ? 'rgba(0, 217, 255, 0.05)' : 'var(--surface-elevated)',
                cursor: isTavilyAvailable ? 'pointer' : 'not-allowed',
                opacity: isTavilyAvailable ? 1 : 0.5,
              }}
            >
              <input
                type="radio"
                name="modeChoice"
                value="live"
                checked={searchMode === 'live'}
                onChange={() => isTavilyAvailable && setSearchMode('live')}
                disabled={!isTavilyAvailable}
                style={{ marginTop: '0.25rem' }}
              />
              <div>
                <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>Tavily Live Web Search</strong>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  {isTavilyAvailable
                    ? 'Cloud-indexed technical search enabled.'
                    : 'Set TAVILY_API_KEY in .env to enable.'}
                </div>
              </div>
            </label>

            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.65rem',
                padding: '0.85rem',
                border: `1px solid ${searchMode === 'fixture' ? 'var(--warning)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-sm)',
                background: searchMode === 'fixture' ? 'rgba(255, 181, 71, 0.05)' : 'var(--surface-elevated)',
                cursor: 'pointer',
              }}
            >
              <input
                type="radio"
                name="modeChoice"
                value="fixture"
                checked={searchMode === 'fixture'}
                onChange={() => setSearchMode('fixture')}
                style={{ marginTop: '0.25rem' }}
              />
              <div>
                <strong style={{ color: 'var(--warning)', fontSize: '0.9rem' }}>Simulated Fixture Mode</strong>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Deterministic offline fixtures for evaluation and synthetic testing.
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Investigation Target Form */}
      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: '1.25rem' }}>
          <div className="card-header">
            <span className="card-title">Target Supplier Profile</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className={`btn ${formSupplierMode === 'new' ? 'btn-primary' : 'btn-outline'}`}
                style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}
                onClick={() => setFormSupplierMode('new')}
              >
                + New Supplier
              </button>
              <button
                type="button"
                className={`btn ${formSupplierMode === 'existing' ? 'btn-primary' : 'btn-outline'}`}
                style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}
                onClick={() => setFormSupplierMode('existing')}
              >
                Select Existing
              </button>
            </div>
          </div>

          <div className="card-body">
            {formSupplierMode === 'existing' ? (
              <div className="form-group">
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
                      {s.name} ({s.country_or_region || 'Unknown Country'}) — Criticality: {s.criticality}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Supplier Corporate Name *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. BASF SE, TSMC, or Micron Technology"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Country / Jurisdiction</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Germany, Taiwan, or United States"
                      value={formCountry}
                      onChange={(e) => setFormCountry(e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Official Domain (for Entity Resolution)</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. basf.com or tsmc.com"
                      value={formDomain}
                      onChange={(e) => setFormDomain(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
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
              </>
            )}
          </div>
        </div>

        {/* Buyer Exposure Context */}
        <div className="card" style={{ marginBottom: '1.25rem' }}>
          <div className="card-header">
            <span className="card-title">Buyer Inventory & Recovery Context (Optional)</span>
            <span className="pill pill-neutral">Formula EX-003</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
              Operational gap is calculated deterministically as <code>Gap = max(0, Disruption - Coverage)</code>. Missing fields remain unknown without being fabricated.
            </p>
            <div className="grid-3">
              <div className="form-group">
                <label className="form-label">Critical Part / Component Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Electronic Chemical Precursor"
                  value={formPartName}
                  onChange={(e) => setFormPartName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Inventory Coverage (Days)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="e.g. 14"
                  value={formCoverageDays}
                  onChange={(e) => setFormCoverageDays(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Expected Recovery (Days)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="e.g. 45"
                  value={formRecoveryDays}
                  onChange={(e) => setFormRecoveryDays(e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Categories Allowlist */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <span className="card-title">Incident Category Filters</span>
            <span className="pill pill-neutral">Allowlist Verified</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
              {[
                { id: 'operational_disruption', label: 'Operational Disruption (Fire, Power, Outage)' },
                { id: 'environmental_regulatory', label: 'Environmental & Regulatory (EPA, Sanctions)' },
                { id: 'logistics_disruption', label: 'Logistics Disruption (Port, Freight, Rail)' },
              ].map((cat) => (
                <label key={cat.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
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
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{cat.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ padding: '0.65rem 1.75rem', fontSize: '0.92rem' }}
            disabled={isPending}
          >
            {isPending ? 'Executing Investigation Pipeline…' : 'Start Live Investigation →'}
          </button>
        </div>
      </form>
    </div>
  )
}
