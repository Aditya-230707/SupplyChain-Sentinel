import { useState } from 'react'
import type { SupplierListItem } from '../lib/api'

interface SuppliersViewProps {
  suppliers: SupplierListItem[]
  total: number
  onInvestigate: (supplier: SupplierListItem) => void
  onAddSupplier: () => void
}

export function SuppliersView({
  suppliers,
  total,
  onInvestigate,
  onAddSupplier,
}: SuppliersViewProps) {
  const [filterQuery, setFilterQuery] = useState('')

  const filtered = suppliers.filter((s) => {
    if (!filterQuery.trim()) return true
    const q = filterQuery.toLowerCase()
    return (
      s.name.toLowerCase().includes(q) ||
      (s.country_or_region && s.country_or_region.toLowerCase().includes(q)) ||
      s.aliases.some((a) => a.toLowerCase().includes(q))
    )
  })

  return (
    <div>
      {/* Header & Action */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            Suppliers
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', marginTop: '0.25rem' }}>
            Registered supply chain partners and critical component sources.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input
            type="search"
            placeholder="Search suppliers or regions…"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="form-input"
            style={{ width: '240px', padding: '0.45rem 0.75rem', fontSize: '0.82rem' }}
          />
          <button className="btn btn-primary" onClick={onAddSupplier} type="button">
            + Add Supplier
          </button>
        </div>
      </div>

      {/* Supplier List Panel */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">
            <span>Supplier Registry</span>
            <span className="badge badge-neutral">{total} Registered</span>
          </span>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Supplier Name</th>
                <th>Region / Jurisdiction</th>
                <th>Criticality Tier</th>
                <th>Registered Date</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((sup) => (
                <tr key={sup.id}>
                  <td>
                    <div>
                      <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{sup.name}</strong>
                      {sup.aliases.length > 0 && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                          Known as: {sup.aliases.join(', ')}
                        </div>
                      )}
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                    {sup.country_or_region || 'Unknown'}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        sup.criticality === 'high'
                          ? 'badge-urgent'
                          : sup.criticality === 'medium'
                          ? 'badge-caution'
                          : 'badge-neutral'
                      }`}
                      style={{ textTransform: 'capitalize' }}
                    >
                      {sup.criticality}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    {new Date(sup.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.3rem 0.7rem', fontSize: '0.78rem' }}
                      onClick={() => onInvestigate(sup)}
                      type="button"
                    >
                      Investigate Disruption →
                    </button>
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-muted)' }}>
                    <div style={{ maxWidth: '360px', margin: '0 auto' }}>
                      <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem', opacity: 0.7 }}>🏢</div>
                      <p style={{ fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                        {filterQuery ? 'No matching suppliers found' : 'No suppliers registered yet'}
                      </p>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                        {filterQuery
                          ? 'Try adjusting your search query.'
                          : 'Add suppliers to track their news mentions and evaluate supply chain vulnerabilities.'}
                      </p>
                      {!filterQuery && (
                        <button className="btn btn-primary" onClick={onAddSupplier} type="button">
                          Add First Supplier
                        </button>
                      )}
                    </div>
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
