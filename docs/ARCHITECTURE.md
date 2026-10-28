# SupplyChain Sentinel — Advanced Architecture Specification

## Overview
SupplyChain Sentinel is an evidence-first supplier incident intelligence platform designed for the Nebius × NVIDIA Global AI Hackathon 2026.

## Non-Negotiable Architectural Principles
1. **Evidence First:** All claims link to verifiable public sources. Model-generated text cannot state facts without cited source evidence.
2. **Determinism over LLM Prose:** Calculations (inventory gap, exposure bands) and policy enforcement use deterministic Python code, never LLM hallucination.
3. **Evidence Graph Provenance:** Every claim, source, supplier, facility, part, and decision is connected in an inspectable bipartite Directed Acyclic Graph (DAG) with explicit semantic relations (`CORROBORATES`, `CONTRADICTS`, `ECHOES`).
4. **Range & Decision Loss Foundations:** Propagates duration uncertainty $[D_{\min}, D_{\max}] \to [\text{gap}_{\min}, \text{gap}_{\max}]$, models deterministic scenarios (Short, Baseline, Extended), and minimizes expected decision loss $\mathbb{E}[L(a)]$.
5. **Bounded Next-Best-Investigation (VOI):** Proactively identifies unresolved evidence gaps and executes bounded follow-up inquiries ranked by transparent Heuristic Value of Information.
6. **No Autonomous High-Impact Actions:** Recommendations require human review. No autonomous supplier suspension or ERP order mutation.
7. **Provider Portability:** Standardized `LLMProvider` interface supports production `NebiusTokenFactoryProvider` (cloud inference with NVIDIA open-weights foundation models) and deterministic `FakeLLMProvider` (offline testing).

## Component Architecture

```text
React 18 + TypeScript (Industrial Telemetry UI)
         │
         ▼ (HTTP / REST)
FastAPI Modular Monolith (/api/v1)
  ├── Core (Config, Structured Logging, Typed Errors)
  ├── DB Layer (SQLAlchemy 2.x Async + SQLite/Postgres)
  │     ├── Models: Suppliers, Parts, Facilities, Runs, Sources, Lineage
  │     └── Models: Claims, ClaimRelations, Incidents, Exposure, Policy, Reviews, Audit
  ├── Providers
  │     ├── LLM: Nebius Token Factory (NVIDIA Nemotron), Fake (offline tests)
  │     ├── Search: DuckDuckGo Live Search, Tavily Search adapter, Fixture Search
  │     └── Content: DuckDuckGo Content Extract, Tavily Extract adapter
  └── Decision Intelligence Pipeline
        ├── URL Normalization & Source Lineage (E-001..E-008)
        ├── Structured Claim Extraction (JSON Schema + quote match)
        ├── Multi-Signal Entity & Facility Resolution (ID-001..ID-005, FAC-001)
        ├── Semantic Claim Relations & Contradiction Detection (CR-001..CR-004)
        ├── Mathematical Exposure & Decision Loss Engine (EX-001..EX-009)
        ├── Deterministic Policy Rulebook (P-001..P-010)
        ├── Evidence Graph DAG Builder (Bipartite Graph & Provenance Ledger)
        ├── Bounded Next-Best-Investigation Loop (VOI Ranking & Gap Closure)
        └── Decision Gate & Immutable Audit Ledger
```

## Security & Secrets
- All secrets are loaded from environment variables (`.env`).
- `.env` is gitignored; `.env.example` contains only non-sensitive placeholders.
- API endpoints and logs redact credentials and prompt payloads.
- DuckDuckGo content extractor includes strict SSRF safeguards against private IPs and loopback interfaces.
