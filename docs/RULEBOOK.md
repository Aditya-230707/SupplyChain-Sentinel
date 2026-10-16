# SupplyChain Sentinel — Rulebook v1

This document specifies the deterministic policy and evidence evaluation rules implemented in Sentinel.

## 1. Evidence Rules (E-Series)
- **E-001 (Canonical URL Deduplication):** Identical canonical URLs are merged into a single source document.
- **E-002 (Near-Duplicate Candidates):** High title/content similarity marks potential duplicate relations without erasing source URLs.
- **E-003 (Shared-Origin Reporting):** Wire service/press release syndications are linked to common origin; counted as single reporting group.
- **E-004 (Snippet-Only Limitation):** Sources with only search snippets cannot support claims beyond the snippet.
- **E-005 (Quote Exact Match):** Extracted supporting quotes must be exact substrings of stored source text.
- **E-006 (Source-Class Context):** Official notices verify regulatory action occurred, not necessarily private disputed allegations.
- **E-007 (Missing is Not False):** Inaccessible sources or absent results do not prove no incident occurred.
- **E-008 (Event vs Publication Date):** Event dates and publication dates are strictly tracked as separate attributes.

## 2. Identity Resolution Rules (ID-Series)
- **ID-001 (Name-Only Ambiguity):** Common names without domain/registry/facility confirmation cannot achieve `confirmed` status.
- **ID-002 (Multi-Signal Confirmation):** Domain, registry ID, or multiple compatible independent signals required for `confirmed`.
- **ID-003 (Corporate Affiliation):** Subsidiary/parent relations must be explicitly documented; incidents at affiliates do not automatically attach.
- **ID-004 (Ambiguity Blocks Action):** Matches marked `ambiguous`, `mismatch`, or `unknown` block strong recommendations.
- **ID-005 (Transparent Signals):** All identity decisions expose matched signals and missing/unresolved signals.

## 3. Evidence State Rules (EV-Series)
- **EV-001 (Single Origin):** One reporting group maps to `single_source` or `unverified`.
- **EV-002 (Corroboration):** Requires >=2 distinct reporting groups with independent origin.
- **EV-003 (Disputed Evidence):** Contradictory evidence creates a review candidate.
- **EV-004 (Allegation Framing):** Allegations remain allegations unless official finding is documented.
- **EV-005 (Resolution Supersession):** Verified resolution supersedes active disruption status.
- **EV-006 (No LLM Truth Override):** LLM judgment cannot promote unverified claims without evidence.

## 4. Business Exposure Rules (EX-Series)
- **EX-001 (Relevance Proof):** Supplier-part relationship required to calculate business exposure.
- **EX-002 (Null Safety):** Missing recovery days or coverage days yields `null` gap days, never `0`.
- **EX-003 (Deterministic Gap Formula):** `gap_days = max(0, disruption_duration_days - inventory_coverage_days)`.
- **EX-004 (Criticality Routing):** High criticality increases review priority, not evidence truth.
- **EX-005 (Category Separation):** Severity, evidence state, and business exposure are non-interchangeable.
- **EX-006 (Provenance Tagging):** Scenario assumptions vs source-backed values are explicitly distinguished.

## 5. Recommendation Rules (P-Series)
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
