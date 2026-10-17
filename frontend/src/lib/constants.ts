export interface BenchmarkScenario {
  key: string
  title: string
  badge: string
  badgeClass: string
  supplierName: string
  country: string
  domain: string
  partName: string
  coverage: string
  recovery: string | null
  criticality: 'low' | 'medium' | 'high' | 'unknown'
  summary: string
}

export const BENCHMARK_SCENARIOS: BenchmarkScenario[] = [
  {
    key: 'dresden',
    title: 'Benchmark A: Genuine Disruption',
    badge: 'Urgent Review Expected',
    badgeClass: 'pill-danger',
    supplierName: 'Silicon Foundry Dresden GmbH',
    country: 'Germany',
    domain: 'silicon-dresden.de',
    partName: 'Automotive Microcontroller MCU-4',
    coverage: '14',
    recovery: '45',
    criticality: 'high',
    summary:
      'Wafer fab cleanroom fire halting 300mm output for 45 days. Buyer has 14-day stock, resulting in a 31-day operational gap.',
  },
  {
    key: 'titan',
    title: 'Benchmark B: True Non-Impacting Incident',
    badge: 'Contingency / Monitor',
    badgeClass: 'pill-warning',
    supplierName: 'Titan Energy Solutions',
    country: 'United States',
    domain: 'titan-energy.com',
    partName: 'Battery Module Pack-B',
    coverage: '30',
    recovery: '10',
    criticality: 'medium',
    summary:
      'Transformer explosion at regional distribution substation with zero manufacturing plant or assembly impact.',
  },
  {
    key: 'vertex',
    title: 'Benchmark C: Name / Entity Mismatch',
    badge: 'Identity Blocker Expected',
    badgeClass: 'pill-neutral',
    supplierName: 'Vertex Components Ltd',
    country: 'United Kingdom',
    domain: 'vertex-components.co.uk',
    partName: 'Industrial Fastener Steel Bolt',
    coverage: '60',
    recovery: null,
    criticality: 'low',
    summary:
      'Cyber incident reported on "Vertex Ltd" based in Melbourne, Australia. Entity resolution flags geographic contradiction, blocking false escalation.',
  },
]

export type ActiveTab =
  | 'investigations'
  | 'new_investigation'
  | 'workspace'
  | 'suppliers'
  | 'evidence'
  | 'decision'
  | 'audit'
  | 'telemetry'
