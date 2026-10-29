import { useState } from 'react'

interface UserManualViewProps {
  onStartInvestigation: () => void
  onViewSuppliers: () => void
}

export function UserManualView({ onStartInvestigation, onViewSuppliers }: UserManualViewProps) {
  const [activeSection, setActiveSection] = useState<'screen_guide' | 'concepts' | 'scenarios' | 'faq'>('screen_guide')

  return (
    <div className="main-content">
      {/* Header */}
      <div className="panel" style={{ marginBottom: '1.25rem', borderLeft: '4px solid var(--accent)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1.25rem' }}>
            <img
              src="/logo.png"
              alt="Sentinel Logo"
              style={{ width: '56px', height: '56px', objectFit: 'contain', flexShrink: 0, marginTop: '4px' }}
            />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
                <span className="badge badge-verified" style={{ fontSize: '0.75rem' }}>Operator Manual</span>
                <span className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>Nebius × NVIDIA Nemotron</span>
              </div>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                SupplyChain Sentinel — Operator Guide & Screen Manual
              </h1>
              <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '720px', fontSize: '0.88rem' }}>
                Exact walkthrough matching every form field, toggle button, and dropdown in the application.
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={onStartInvestigation} type="button">
              Go To Investigation Screen →
            </button>
            <button className="btn btn-outline" onClick={onViewSuppliers} type="button">
              View Suppliers (26)
            </button>
          </div>
        </div>

        {/* Tab Selector */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
          {[
            { id: 'screen_guide', label: '1. Screen-by-Screen Form Guide' },
            { id: 'scenarios', label: '2. The 3 Sample Scenarios' },
            { id: 'concepts', label: '3. Verification Rules (Rulebook)' },
            { id: 'faq', label: '4. Diagnostics & FAQ' },
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

      {/* Section 1: Exact Screen Guide matching user screenshot */}
      {activeSection === 'screen_guide' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Top Bar Quick Pre-Fill */}
          <div className="panel" style={{ borderLeft: '4px solid var(--status-caution-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <span className="badge badge-caution">Top Right Feature</span>
              <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                Sample Scenario Dropdown
              </strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              At the very top right of the <em>New Supplier Investigation</em> screen, look for <strong>Sample Scenario: [ Select scenario to pre-fill… ]</strong>. Selecting one automatically populates the entire form and selects <strong>Deterministic Fixtures</strong> so you can test the pipeline instantly without typing anything!
            </p>
          </div>

          {/* Form Breakdown */}
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
              Form Field Reference (Matching Your Screen Exactly)
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Section 1 */}
              <div style={{ padding: '0.9rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '0.9rem' }}>1. Search & Discovery Engine</span>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.5rem' }}>
                  Choose where Sentinel gathers incident intelligence:
                </p>
                <ul style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
                  <li><strong>DuckDuckGo Live (Checked by default):</strong> Scours the live public web for real-time news with built-in SSRF protection. Zero API keys needed.</li>
                  <li><strong>Deterministic Fixtures:</strong> Runs reproducible offline test cases (e.g. Dresden wafer fire, Titan substation). Best for verifying model logic immediately.</li>
                  <li><strong>Tavily Search:</strong> Premium structured news engine (requires <code>TAVILY_API_KEY</code>).</li>
                </ul>
              </div>

              {/* Section 2 */}
              <div style={{ padding: '0.9rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '0.9rem' }}>2. Target Supplier</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Top buttons: [Enter Details] | [Select Existing (26)]</span>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.5rem' }}>
                  You can either enter a new supplier or pick one of the 26 pre-loaded suppliers:
                </p>
                <ul style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
                  <li><strong>Click [Select Existing (26)]:</strong> Opens a dropdown where you can choose a vendor from your database (e.g., <em>Silicon Foundry Dresden GmbH</em>).</li>
                  <li><strong>Click [Enter Details]:</strong> Manually enter <em>Supplier Legal Name *</em> (required), <em>Country / Jurisdiction</em>, <em>Official Domain</em> (used for Rule ID-001 website matching), and <em>Criticality Tier</em> (Tier 1 High, Tier 2 Medium, Tier 3 Low).</li>
                </ul>
              </div>

              {/* Section 3 */}
              <div style={{ padding: '0.9rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '0.9rem' }}>3. Operational Exposure Context (Optional)</span>
                  <span className="badge badge-neutral">Formula EX-003</span>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.5rem' }}>
                  Mathematical inventory formula: <code>Gap = max(0, Disruption Duration − Safety Stock)</code>.
                </p>
                <ul style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
                  <li><strong>Critical Component / Part Name:</strong> e.g., <code>Automotive Microcontroller MCU-4</code>. Identifies which part is at risk.</li>
                  <li><strong>Safety Stock Coverage (Days):</strong> e.g., <code>14</code>. How many days your plant can continue operating using warehouse reserves.</li>
                  <li><strong>Estimated Disruption (Days):</strong> e.g., <code>45</code>. The expected vendor downtime reported in news or estimated by the model.</li>
                  <li><em>Result:</em> If Disruption (45) &gt; Safety Stock (14), Sentinel calculates a <strong>31-Day Operational Gap</strong>.</li>
                </ul>
              </div>

              {/* Section 4 & Submit */}
              <div style={{ padding: '0.9rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '0.9rem' }}>4. Incident Categories to Monitor & Launch</span>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.35rem 0 0.5rem 0', lineHeight: 1.5 }}>
                  Select incident categories: <em>Operational Disruption</em> (fires/outages), <em>Environmental & Regulatory</em> (sanctions/EPA), or <em>Logistics Disruption</em> (ports/freight).
                </p>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                  Finally, click the green button at the bottom right: <code>[Start Investigation →]</code>.
                </p>
              </div>
            </div>
          </div>

          {/* What happens next */}
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              What Happens After Clicking "Start Investigation →"?
            </h2>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '0.75rem' }}>
              Sentinel immediately displays the dedicated <strong>Gathering Details Loading Screen</strong> followed by the <strong>Forensic Workspace</strong>:
            </p>
            <ol style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
              <li><strong>Gathering Details Loading Screen:</strong> Shows live elapsed seconds and an animated 5-stage pipeline tracker: <em>Source Ingestion → Wire Deduplication → Nebius Cloud Neural Reasoning (NVIDIA Nemotron) → Verbatim Quote Grounding → Operational Exposure Math</em>.</li>
              <li><strong>Forensic Evidence Cards:</strong> Once completed, green <code>validated</code> pills display each extracted claim with verified character offsets inside the original source documents.</li>
              <li><strong>Syndicated Lineage:</strong> Groups news wire duplicates (Reuters/Yahoo/MSN) into a single reporting cluster to prevent artificial confidence inflation.</li>
              <li><strong>Human Decision Gate:</strong> Review the deterministic policy recommendation (e.g. <em>Invoke Dual Sourcing</em> or <em>Monitor Only</em>), select <em>Approve</em>, <em>Override</em>, or <em>Dismiss</em>, enter your reviewer credentials, and click <strong>Commit Review Decision</strong> to write to the permanent Audit Trail.</li>
            </ol>
          </div>
        </div>
      )}

      {/* Section 2: Sample Scenarios */}
      {activeSection === 'scenarios' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="panel">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
              How to Test the 3 Built-in Benchmark Scenarios
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1rem' }}>
              Select these directly from the <strong>Sample Scenario</strong> dropdown on the New Investigation screen:
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <span className="badge badge-urgent" style={{ marginBottom: '0.5rem', display: 'inline-block' }}>Urgent Review</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>1. Cleanroom Fire (Dresden)</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.4rem 0', lineHeight: 1.5 }}>
                  Select <code>Cleanroom Fire (Direct Disruption) (Silicon Foundry Dresden GmbH)</code>. Pre-fills 14 days safety stock and 45 days disruption.
                </p>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  <strong>Result:</strong> 31-day net operational gap triggers Rule P-007 (Invoke Dual Sourcing).
                </p>
              </div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <span className="badge badge-caution" style={{ marginBottom: '0.5rem', display: 'inline-block' }}>Monitor Only</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>2. Substation Incident (Titan)</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.4rem 0', lineHeight: 1.5 }}>
                  Select <code>Substation Incident (Non-Impacting) (Titan Energy Solutions)</code>. Pre-fills 30 days safety stock and 10 days recovery.
                </p>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  <strong>Result:</strong> Transformer explosion was off-site; manufacturing lines unaffected. Net gap is 0 days. Triggers Rule P-009 (Monitor Only), suppressing false panic.
                </p>
              </div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-base)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)' }}>
                <span className="badge badge-neutral" style={{ marginBottom: '0.5rem', display: 'inline-block' }}>Entity Mismatch</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>3. Cybersecurity Alert (Vertex)</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0.4rem 0', lineHeight: 1.5 }}>
                  Select <code>Cybersecurity Alert (Entity Mismatch) (Vertex Components Ltd)</code>.
                </p>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  <strong>Result:</strong> News is about a company in Australia, whereas your vendor is in the UK. Rule ID-001 catches the geographic mismatch and blocks wrongful escalation.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Concepts */}
      {activeSection === 'concepts' && (
        <div className="panel">
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
            The Deterministic Rulebook Safeguards
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <strong>Rule E-005 (Exact Substring Verification):</strong> No quote is trusted without an exact character match against the raw HTML/text payload.
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <strong>Rules E-001–E-003 (Syndicated Wire Deduplication):</strong> News stories citing the same original wire service (e.g. Reuters, AP) are grouped into 1 reporting cluster.
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <strong>Rules ID-001–ID-005 (Entity Disambiguation):</strong> Confirms legal name, official web domain, and facility city to prevent mistaking homonyms for your suppliers.
            </div>
          </div>
        </div>
      )}

      {/* Section 4: FAQ */}
      {activeSection === 'faq' && (
        <div className="panel">
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.85rem' }}>
            Diagnostics & FAQ
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <strong>Where can I see Nebius model latency?</strong> Click <em>System Diagnostics</em> at the bottom of the left sidebar to see real-time Nebius Token Factory roundtrip ping.
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
              <strong>Do I need API keys to run live investigations?</strong> No! <em>DuckDuckGo Live</em> mode executes real internet searches with zero API keys required.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
