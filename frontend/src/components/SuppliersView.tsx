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
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Supplier Registry & Exposure Profiles
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
            Registered supply chain nodes with verified domains and operational dependencies.
          </p>
        </div>
        <button className="btn btn-primary" onClick={onAddSupplier}>
          + Add Supplier
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Registered Suppliers</span>
          <span className="pill pill-neutral">{total} Registered</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Supplier Name</th>
                <th>Region</th>
                <th>Criticality</th>
                <th>Registered Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((sup) => (
                <tr key={sup.id}>
                  <td>
                    <strong style={{ color: 'var(--text-primary)' }}>{sup.name}</strong>
                    {sup.aliases.length > 0 && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Aliases: {sup.aliases.join(', ')}
                      </div>
                    )}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{sup.country_or_region || 'Unknown'}</td>
                  <td>
                    <span
                      className={`pill ${
                        sup.criticality === 'high'
                          ? 'pill-danger'
                          : sup.criticality === 'medium'
                          ? 'pill-warning'
                          : 'pill-neutral'
                      }`}
                    >
                      {sup.criticality.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(sup.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <button
                      className="btn btn-primary"
                      style={{ padding: '0.25rem 0.65rem', fontSize: '0.78rem' }}
                      onClick={() => onInvestigate(sup)}
                    >
                      Investigate Now
                    </button>
                  </td>
                </tr>
              ))}
              {suppliers.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No suppliers registered yet.
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
