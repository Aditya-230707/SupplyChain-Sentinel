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
    title: 'Cleanroom Fire (Direct Disruption)',
    badge: 'Urgent Review',
    badgeClass: 'badge-urgent',
    supplierName: 'Silicon Foundry Dresden GmbH',
    country: 'Germany',
    domain: 'silicon-dresden.de',
    partName: 'Automotive Microcontroller MCU-4',
    coverage: '14',
    recovery: '45',
    criticality: 'high',
    summary:
      'Wafer fab cleanroom fire halting 300mm output for 45 days. With 14-day safety inventory, results in a 31-day operational gap.',
  },
  {
    key: 'titan',
    title: 'Substation Incident (Non-Impacting)',
    badge: 'Monitor Only',
    badgeClass: 'badge-caution',
    supplierName: 'Titan Energy Solutions',
    country: 'United States',
    domain: 'titan-energy.com',
    partName: 'Battery Module Pack-B',
    coverage: '30',
    recovery: '10',
    criticality: 'medium',
    summary:
      'Transformer explosion at regional distribution substation with zero manufacturing plant or assembly line impact.',
  },
  {
    key: 'vertex',
    title: 'Cybersecurity Alert (Entity Mismatch)',
    badge: 'Entity Mismatch',
    badgeClass: 'badge-neutral',
    supplierName: 'Vertex Components Ltd',
    country: 'United Kingdom',
    domain: 'vertex-components.co.uk',
    partName: 'Industrial Fastener Steel Bolt',
    coverage: '60',
    recovery: null,
    criticality: 'low',
    summary:
      'Cyber incident reported on "Vertex Ltd" based in Melbourne, Australia. Geographic disambiguation prevents false escalation.',
  },
]

export type ActiveTab =
  | 'investigations'
  | 'new_investigation'
  | 'workspace'
  | 'suppliers'
  | 'audit'
