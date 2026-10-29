import { useState } from 'react'

interface UserManualViewProps {
  onStartInvestigation: () => void
  onViewSuppliers: () => void
}

export function UserManualView({ onStartInvestigation, onViewSuppliers }: UserManualViewProps) {
  const [activeSection, setActiveSection] = useState<'quickstart' | 'concepts' | 'screens' | 'scenarios' | 'faq'>('quickstart')

  return (
    <div className="main-content">
      {/* Header */}
      <div className="panel" style={{ marginBottom: '1.25rem', borderLeft: '4px solid var(--accent)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
              <span className="badge badge-verified" style={{ fontSize: '0.75rem' }}>Operator Guide</span>
              <span className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>Nebius × NVIDIA Nemotron</span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              SupplyChain Sentinel — User Manual & Operations Guide
            </h1>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '720px', fontSize: '0.9rem' }}>
              Complete reference manual for monitoring supplier disruption signals, conducting evidence-first investigations, evaluating operational inventory exposure, and recording auditable procurement decisions.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={onStartInvestigation} type="button">
              + Launch Investigation
            </button>
            <button className="btn btn-outline" onClick={onViewSuppliers} type="button">
              Manage Suppliers
            </button>
          </div>
        </div>

        {/* Tab Selector */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
          {[
            { id: 'quickstart', label: '1. Quick Start (4-Step Flow)' },
            { id: 'concepts', label: '2. Core Principles & Safeguards' },
            { id: 'screens', label: '3. Interface Walkthrough' },
            { id: 'scenarios', label: '4. Benchmark Scenarios' },
            { id: 'faq', label: '5. Troubleshooting & FAQ' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id as typeof activeSection)}
              className={`btn ${activeSection === tab.id ? 'btn-primary' : 'btn-outline'}`}
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Section 1: Quick Start */}
      {activeSection === 'quickstart' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
              How to Run an Incident Investigation in 4 Steps
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
              <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent)', color: '#fff', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                  1
                </div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                  Select or Enter Supplier
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Click <strong>New Investigation</strong>. Pick an existing tracked vendor (e.g. <em>Silicon Foundry Dresden</em>) or type a new vendor name, country, and official web domain.
                </p>
              </div>

              <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent)', color: '#fff', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                  2
                </div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                  Input Inventory Buffer
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Enter your internal <strong>Days of Inventory Coverage</strong> (e.g. 14 days). Sentinel mathematically balances this against reported downtime to calculate true disruption exposure.
                </p>
              </div>

              <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent)', color: '#fff', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                  3
                </div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                  Launch Pipeline
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Select search engine (<strong>DuckDuckGo Live</strong> or <strong>Tavily</strong>) and click <strong>Run Investigation</strong>. Sentinel executes multi-stage verification in real-time.
                </p>
              </div>

              <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent)', color: '#fff', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                  4
                </div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                  Inspect & Record Decision
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Review exact substring quote matches, syndicated wire clusters, and policy advice. Sign off on the Decision Gate to commit the decision to the immutable audit trail.
                </p>
              </div>
            </div>
          </div>

          <div className="panel" style={{ background: 'var(--bg-surface-elevated)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Pro Tip: 1-Click Evaluation Scenarios
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.85rem' }}>
              Want to see how Sentinel handles edge cases immediately? In the <strong>New Investigation</strong> screen, click any of the scenario cards at the top:
            </p>
            <ul style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
              <li><strong>Cleanroom Fire (Dresden):</strong> Shows genuine factory downtime (45 days) outpacing safety stock (14 days), triggering an <em>Invoke Dual Sourcing</em> recommendation.</li>
              <li><strong>Substation Incident (Titan Energy):</strong> Disruption occurred at an off-site power substation without damaging production lines, demonstrating how Sentinel rules out false alarms.</li>
              <li><strong>Cybersecurity Alert (Vertex):</strong> Disruption occurred at an unrelated entity in Australia with an identical name, demonstrating multi-signal entity disambiguation.</li>
            </ul>
          </div>
        </div>
      )}

      {/* Section 2: Core Concepts */}
      {activeSection === 'concepts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
              Why Sentinel is Different from Raw LLM Summarizers
            </h2>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1.25rem' }}>
              Generic AI models panic on negative keywords, treat syndicated news copies as independent verification, and hallucinate quotes. Sentinel enforces mathematical, deterministic safeguards on top of <strong>NVIDIA Nemotron-3.5-Lightning</strong>:
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '0.9rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <div style={{ fontWeight: 600, color: 'var(--status-verified)', marginBottom: '0.25rem' }}>
                  Rule E-005: Exact Substring Quote Grounding
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Every extracted fact or downtime claim must contain an exact, character-level substring match against the fetched article body. If a model fabricates or paraphrases text, the claim is flagged as <code>quote_mismatch</code> and discarded.
                </p>
              </div>

              <div style={{ padding: '0.9rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <div style={{ fontWeight: 600, color: 'var(--status-verified)', marginBottom: '0.25rem' }}>
                  Rules E-001–E-003: Syndicated Wire Deduplication
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  When Reuters distributes a story reprinted by Yahoo, MSN, and Investing.com, naive algorithms count this as "4 independent sources." Sentinel parses canonical URLs, wire bylines, and text hashes into a single reporting group.
                </p>
              </div>

              <div style={{ padding: '0.9rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <div style={{ fontWeight: 600, color: 'var(--status-verified)', marginBottom: '0.25rem' }}>
                  Rules ID-001–ID-005: Multi-Signal Entity Resolution
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  To attribute an incident to a supplier, Sentinel requires corroborating corporate domain, plant location, or country signals. Homonym companies in different industries or geographies are safely marked as mismatches.
                </p>
              </div>

              <div style={{ padding: '0.9rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <div style={{ fontWeight: 600, color: 'var(--status-verified)', marginBottom: '0.25rem' }}>
                  Bounded Range Exposure Arithmetic
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Disruptions are represented as bounded intervals [min, max] rather than false point estimates. If duration is unknown, the operational gap is strictly preserved as null rather than defaulted to zero.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Interface Walkthrough */}
      {activeSection === 'screens' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
              Tour of System Screens
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '0.35rem' }}>
                  A. Investigations List
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  The central monitoring inbox. Lists all past and running investigations with real-time status indicators (<code>queued</code>, <code>searching</code>, <code>extracting</code>, <code>completed</code>), severity badges (<em>Urgent Review</em>, <em>Action Recommended</em>, <em>Monitor Only</em>), and one-click access to the active workspace.
                </p>
              </div>

              <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '0.35rem' }}>
                  B. Active Investigation Workspace (3-Pane Investigation View)
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.5rem' }}>
                  The core forensic workstation divided into high-density analysis zones:
                </p>
                <ul style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
                  <li><strong>Incident Summary & Severity:</strong> Shows the resolved supplier, facility, incident category, and calculated operational gap (Days to Recover minus Inventory Buffer).</li>
                  <li><strong>Evidence & Quote Inspection:</strong> Card-by-card breakdown of every extracted claim. Click any quote to inspect its exact character offset within the source article.</li>
                  <li><strong>Lineage & Syndication Grouping:</strong> Visual inspection of primary publisher vs syndication copies.</li>
                  <li><strong>Human Decision Gate:</strong> The procurement sign-off panel. Select your action, provide reviewer credentials and context, and submit to the audit log.</li>
                </ul>
              </div>

              <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '0.35rem' }}>
                  C. Suppliers Directory
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Manage the bill of materials and supplier master data. View active parts, manufacturing facilities, safety stock buffers (coverage days), and historical incident frequency per vendor.
                </p>
              </div>

              <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '0.35rem' }}>
                  D. Immutable Audit Trail
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Comprehensive forensic ledger. Every pipeline search query, model extraction, policy rule evaluation, and human decision gate sign-off is logged with UTC timestamps and correlation IDs.
                </p>
              </div>

              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '0.35rem' }}>
                  E. System Diagnostics Modal
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Accessible from the bottom of the left sidebar. Verifies live connection to <strong>Nebius Token Factory</strong>, checks NVIDIA Nemotron model latency, validates search provider API quotas, and reports database connectivity.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 4: Benchmark Scenarios */}
      {activeSection === 'scenarios' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
              Standard Benchmark Challenge Scenarios
            </h2>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
              These scenarios demonstrate how the rule engine prevents the most dangerous enterprise failure modes:
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <span className="badge badge-urgent" style={{ marginBottom: '0.5rem', display: 'inline-block' }}>Urgent Review</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>1. Dresden Cleanroom Fire</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.4rem 0', lineHeight: 1.5 }}>
                  <strong>Scenario:</strong> 300mm wafer cleanroom fire halting fabrication for 45 days. Inventory buffer is 14 days.
                </p>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  <strong>Expected Outcome:</strong> 31-day operational exposure gap. Triggers Rule P-007 (Invoke Dual Sourcing).
                </p>
              </div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <span className="badge badge-caution" style={{ marginBottom: '0.5rem', display: 'inline-block' }}>Monitor Only</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>2. Titan Substation Explosion</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.4rem 0', lineHeight: 1.5 }}>
                  <strong>Scenario:</strong> Media reports power substation explosion near battery manufacturer plant. Plant backup generators kept lines running.
                </p>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  <strong>Expected Outcome:</strong> Net gap is 0 days. Triggers Rule P-009 (Monitor Only) preventing false panic.
                </p>
              </div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <span className="badge badge-neutral" style={{ marginBottom: '0.5rem', display: 'inline-block' }}>Entity Mismatch</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>3. Vertex Homonym Alert</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.4rem 0', lineHeight: 1.5 }}>
                  <strong>Scenario:</strong> News alert regarding a ransomware attack at "Vertex Ltd" in Australia. Tracked supplier is UK fastener maker.
                </p>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  <strong>Expected Outcome:</strong> Geographic mismatch detected. Escalation blocked, protecting buyer relationships.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 5: FAQ */}
      {activeSection === 'faq' && (
        <div className="panel">
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
            Frequently Asked Questions & Troubleshooting
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '0.85rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
                Q: Which AI model is running under the hood?
              </div>
              <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Sentinel runs on <strong>NVIDIA Nemotron-3.5-Lightning</strong> hosted directly on <strong>Nebius Token Factory</strong> via high-throughput GPU clusters.
              </p>
            </div>

            <div style={{ padding: '0.85rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
                Q: Can I use live public web search without paying for search keys?
              </div>
              <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Yes! The default search engine is <strong>DuckDuckGo Live</strong>, which requires zero API keys and features enterprise SSRF safe guard protection. For news wire searches, Tavily is also supported when an optional key is supplied.
              </p>
            </div>

            <div style={{ padding: '0.85rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
                Q: How does the Decision Gate work?
              </div>
              <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                No automated policy action takes effect without human sign-off. A procurement manager or sourcing engineer must review the evidence, select an action (Approve, Override, Dismiss), provide their name and justification notes, and submit.
              </p>
            </div>

            <div style={{ padding: '0.85rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
                Q: Where is the OpenAPI documentation?
              </div>
              <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Interactive Swagger UI is available at <a href="/api/docs" target="_blank" rel="noreferrer">/api/docs</a> and ReDoc is available at <a href="/api/redoc" target="_blank" rel="noreferrer">/api/redoc</a>.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
