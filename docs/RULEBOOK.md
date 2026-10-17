# SupplyChain Sentinel — Deterministic Rulebook v2

This document specifies the deterministic policy, evidence evaluation, exposure calculation, and Next-Best-Investigation rules implemented in Sentinel.

## 1. Evidence Rules (E-Series)
- **E-001 (Canonical URL Deduplication):** Identical canonical URLs are merged into a single source document.
- **E-002 (Near-Duplicate Candidates):** High title/content similarity marks potential duplicate relations without erasing source URLs.
- **E-003 (Shared-Origin Reporting):** Wire service/press release syndications are linked to common origin; counted as single reporting group.
- **E-004 (Snippet-Only Limitation):** Sources with only search snippets cannot support claims beyond the snippet.
- **E-005 (Quote Exact Match):** Extracted supporting quotes must be exact substrings of stored source text.
- **E-006 (Source-Class Context):** Official notices verify regulatory action occurred, not necessarily private disputed allegations.
- **E-007 (Missing is Not False):** Inaccessible sources or absent results do not prove no incident occurred.
- **E-008 (Event vs Publication Date):** Event dates and publication dates are strictly tracked as separate attributes.

## 2. Identity & Facility Resolution Rules (ID & FAC Series)
- **ID-001 (Name-Only Ambiguity):** Common names without domain/registry/facility confirmation cannot achieve `confirmed` status.
- **ID-002 (Multi-Signal Confirmation):** Domain, registry ID, or multiple compatible independent signals required for `confirmed`.
- **ID-003 (Corporate Affiliation):** Subsidiary/parent relations must be explicitly documented; incidents at affiliates do not automatically attach.
- **ID-004 (Ambiguity Blocks Action):** Matches marked `ambiguous`, `mismatch`, or `unknown` block strong recommendations.
- **ID-005 (Transparent Signals):** All identity decisions expose matched signals and missing/unresolved signals.
- **FAC-001 (Facility Verification):** Incident location is matched against buyer's specific manufacturing plants; damage at non-contracted facilities is isolated as non-impacting.

## 3. Semantic Claim Relations Rules (CR-Series)
- **CR-001 (Contradiction / Resolution):** Claims asserting operational normality or drill exercises contradict disruption claims on the same target, prioritizing official resolution statements.
- **CR-002 (Independent Corroboration):** Claims from distinct reporting groups corroborating the same incident event increase evidence weight.
- **CR-003 (Syndicated Wire Echo):** Claims derived from syndicated wires sharing identical source lineage are classified as echoes rather than independent confirmations.
- **CR-004 (Clarification):** Regulatory or corporate filings clarifying preliminary press reports are categorized as authoritative clarifications.

## 4. Business Exposure & Decision Loss Rules (EX-Series)
- **EX-001 (Relevance Proof):** Supplier-part relationship required to calculate business exposure.
- **EX-002 (Null Safety):** Missing recovery days or coverage days yields `null` gap days, never `0`.
- **EX-003 (Deterministic Gap Formula):** $\text{gap\_days} = \max(0, \text{disruption\_duration\_days} - \text{inventory\_coverage\_days})$.
- **EX-004 (Criticality Routing):** High criticality increases review priority, not evidence truth.
- **EX-005 (Category Separation):** Severity, evidence state, and business exposure are non-interchangeable.
- **EX-006 (Provenance Tagging):** Scenario assumptions vs source-backed values are explicitly distinguished.
- **EX-007 (Range Propagation):** Duration intervals $[D_{\min}, D_{\max}]$ propagate deterministically to inventory gaps $[\text{gap}_{\min}, \text{gap}_{\max}]$.
- **EX-008 (Deterministic Scenarios):** Evaluates Short Interruption (7d), Baseline Grounded ($D$), and Extended Disruption ($D \times 1.5$).
- **EX-009 (Decision Loss Minimization):** Minimizes $\mathbb{E}[L(a)] = \text{cost}(a) + \sum P(s) \cdot \text{Loss}(a, s)$ under daily downtime costs; computes loss sensitivity sweeps if uncalibrated.

## 5. Policy Recommendation Rules (P-Series)
- **P-001 (Ambiguous Identity):** Yields `insufficient_evidence` or `request_supplier_confirmation`.
- **P-002 (Unverified Single Source):** Yields `monitor` or `request_supplier_confirmation`.
- **P-003 (Disputed Evidence):** Mandatory human review with competing claims presented.
- **P-004 (Unknown Exposure):** Recommend fact-finding/supplier query, not speculative impact.
- **P-005 (Positive Inventory Gap):** Recommend `review_contingency_plan` or `urgent_human_review`.
- **P-006 (Regulatory Action):** Compliance review; no automated legal or contractual termination.
- **P-007 (Resolved Event):** Display historical context without active disruption flags.
- **P-008 (Provider Failure):** Flag data degradation; do not infer negative risk from failure.
- **P-009 (Human Override):** Human decisions logged alongside original system recommendation.
- **P-010 (No Autonomous Action):** Zero autonomous supplier suspensions or order modifications.

## 6. Next-Best-Investigation Rules (VOI-Series)
- **VOI-001 (Evidence Gap Identification):** Automatically detects unresolved gaps: `ambiguous_identity`, `conflicting_claims`, `missing_duration`, `single_unverified_source`, `facility_unresolved`.
- **VOI-002 (Heuristic Value of Information):** Scores candidate queries:
  $$\text{VOI}(q) = 0.35 \cdot \text{Relevance} + 0.35 \cdot \text{Impact} + 0.20 \cdot \text{Quality} - 0.10 \cdot \text{Redundancy}$$
- **VOI-003 (Bounded Iteration):** Bounded to maximum 1–2 targeted searches; terminates immediately if no new information is uncovered.
- **VOI-004 (Trace Accountability):** Persists query, score, newly retrieved sources, and recommendation change status in `metrics_json["investigation_trace"]`.
