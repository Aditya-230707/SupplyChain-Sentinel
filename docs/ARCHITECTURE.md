# SupplyChain Sentinel — Architecture Specification

## Overview
SupplyChain Sentinel is an evidence-first supplier incident intelligence platform designed for the Nebius × NVIDIA Global AI Hackathon 2026.

## Non-Negotiable Architectural Principles
1. **Evidence First:** All claims link to verifiable public sources. Model-generated text cannot state facts without cited source evidence.
2. **Determinism over LLM Prose:** Calculations (inventory gap, exposure bands) and policy enforcement use deterministic Python code, never LLM hallucination.
3. **No Autonomous High-Impact Actions:** Recommendations require human review. No autonomous supplier suspension or ERP order mutation.
4. **Provider Portability:** Standardized `LLMProvider` interface supports local `OllamaProvider` (development) and `NebiusTokenFactoryProvider` (hackathon submission with NVIDIA open-source models).

## Component Architecture

```text
React 18 + TypeScript (Vite)
         │
         ▼ (HTTP / REST)
FastAPI Modular Monolith (/api/v1)
  ├── Core (Config, Structured Logging, Typed Errors)
  ├── DB Layer (SQLAlchemy 2.x Async + SQLite/Postgres)
  ├── Providers
  │     ├── LLM: Ollama (dev), Nebius Token Factory (submission), Fake (tests)
  │     ├── Search: Tavily Search adapter
  │     └── Content: Tavily Extract adapter
  └── Pipeline & Rulebook (Phases 2-5)
        ├── URL Normalization & Source Lineage (E-001..E-008)
        ├── Structured Claim Extraction (JSON Schema + quote match)
        ├── Multi-Signal Entity Resolution (ID-001..ID-005)
        ├── Incident Clustering & Evidence Adjudication (EV-001..EV-006)
        ├── Deterministic Exposure Calculator (EX-001..EX-006)
        ├── Deterministic Policy Engine (P-001..P-010)
        └── Decision Brief Composer & Citation Validator
```

## Security & Secrets
- All secrets are loaded from environment variables (`.env`).
- `.env` is gitignored; `.env.example` contains only non-sensitive placeholders.
- API endpoints and logs redact credentials and prompt payloads.
