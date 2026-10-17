# SupplyChain Sentinel

> **Evidence-First Supplier Incident Intelligence**  
> Built for the *Nebius × NVIDIA Global AI Hackathon 2026*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-green.svg)](https://www.python.org/)
[![React: 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Evaluation: 100% Quote Validity](https://img.shields.io/badge/Quote_Validity-100%25-brightgreen.svg)](evaluation/evaluation_results.json)
[![Evaluation: 0% False Escalation](https://img.shields.io/badge/False_Escalation-0.0%25-brightgreen.svg)](evaluation/evaluation_results.json)

---

## 1. What SupplyChain Sentinel Does

Enterprise supply chain teams are bombarded by breaking news, wire alerts, and social media rumors regarding factory fires, port strikes, and cyberattacks. Generative AI alone frequently hallucinates quotes, conflates same-name companies, treats duplicate syndicated wire releases as independent corroboration, and recommends premature order freezes.

**SupplyChain Sentinel** solves this with an **evidence-first, deterministic verification pipeline**:
1. **Never trusts raw LLM output:** Model extraction is strictly parsed via Pydantic schemas.
2. **Deterministic quote validation:** Every supporting quote extracted by an LLM is mathematically verified as an exact substring against the immutable retrieved source text.
3. **Syndicated wire lineage clustering:** Automatically groups syndicated press releases and wire copies (via URL canonicalization and SHA-256 fingerprinting) so duplicate reporting does not falsely inflate corroboration confidence.
4. **Multi-signal corporate entity resolution:** Resolves legal entity names, stock tickers, corporate domains, and locations to prevent confusing a distinct company with the buyer's supplier.
5. **Deterministic operational exposure calculation:** Inventory coverage, recovery duration, and supplier-part criticality are calculated using explicit numerical formulas. Missing values remain explicitly `None` (unknown) rather than defaulting to zero.
6. **Explicit policy rulebook (P-001 to P-010):** Recommendations (`urgent_human_review`, `review_contingency_plan`, `request_supplier_confirmation`, `monitor`, `insufficient_evidence`) are produced exclusively by deterministic Python code, never by free-form LLM generation.
7. **Human-in-the-loop decision gate:** The system never autonomously halts orders or cancels contracts. Procurement managers inspect evidence, audit source lineage, and record decisions with full historical audit trails.

---

## 2. Architecture & Core Pipeline

```
[Public Reports / News] ───► [Search Provider (Fixture or Tavily)]
                                        │
                                        ▼
                             [Source Normalizer]
                          (Canonical URL + SHA-256 Hash)
                                        │
                                        ▼
                            [Source Lineage Analyzer]
                         (Syndicated Wire Clustering)
                                        │
                                        ▼
                            [LLM Claim Extraction]
                   (Nebius Token Factory / NVIDIA Nemotron / Ollama)
                                        │
                                        ▼
                       [Deterministic Claim Validator]
                      (Substring Quote Verification)
                                        │
                                        ▼
                       [Multi-Signal Entity Resolver]
                  (Domain, Registry, Country, Legal Name)
                                        │
                                        ▼
                     [Deterministic Exposure Calculator]
                       (Lead Time vs Inventory Gap)
                                        │
                                        ▼
                      [Deterministic Policy Rulebook]
                         (Rules P-001 through P-010)
                                        │
                                        ▼
                     [Human Reviewer Decision Gate & Audit]
```

### Deterministic Rulebook Principles
- **E-005 (Quote Integrity):** Any claim whose quote is not found verbatim in the source text is rejected as ungrounded.
- **ID-001 to ID-004 (Entity Disambiguation):** Ambiguous corporate names or location contradictions block high-impact escalation and trigger `request_supplier_confirmation`.
- **EX-001 to EX-006 (Null-Safe Exposure):** If duration or inventory days are unknown, gap is strictly `None`. The system refuses to invent risk numbers.
- **P-001 to P-010 (Policy Gate):** Single uncorroborated reports never trigger emergency order freezes; resolved/drill events trigger `monitor`.

---

## 3. Quick Start (Zero API Keys — 100% Deterministic Demo)

You can run and test SupplyChain Sentinel immediately with zero external API dependencies or cloud accounts.

### Prerequisites
- Python 3.12 or 3.13
- Node.js 18+ and npm
- Git

### Step 1: Clone and Configure
```powershell
git clone https://github.com/Aditya-230707/SupplyChain-Sentinel.git
cd SupplyChain-Sentinel
copy .env.example .env
```
*(By default, `.env` uses `LLM_PROVIDER=fake` and fixture search mode, requiring no keys).*

### Step 2: Start Backend
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000`  
Interactive Swagger Docs: `http://localhost:8000/docs`

### Step 3: Start Frontend
```powershell
cd ..\frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:5173`

### Step 4: Run a Demo Investigation
1. In the UI, click on the pre-seeded supplier **Apex Semiconductor Ltd**.
2. Select **Fixture Mode (Deterministic)**.
3. Click **"Run Incident Investigation"**.
4. Inspect the verified claims, green quote validation badges, wire lineage clustering, and deterministic exposure gap.
5. In the **Human Review Gate**, select "Accept Recommendation" or "Override", provide rationale, and click **"Record Decision"**.
6. Check the persistent **Audit Trail** below.

---

## 4. Cloud Inference: Nebius Token Factory & NVIDIA Models

For hackathon submission and production cloud workflows, Sentinel integrates with **Nebius Token Factory** using NVIDIA open-weights foundation models.

### Nebius Configuration in `.env`
```env
LLM_PROVIDER=nebius
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1/
NEBIUS_API_KEY=your-nebius-api-key-here
NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning
```
*(Alternative supported NVIDIA models: `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b`, or any active model listed in `/v1/models` in your Nebius console).*

### Security & Fault-Tolerance Features
- **Key Redaction:** The API key is stored securely in memory, never logged, and explicitly stripped from error messages if provider exceptions occur.
- **Structured Output Fallback:** Attempts strict `json_schema` mode first, with automated resilience fallback to `json_object` mode if an endpoint lacks schema enforcement.
- **Provider Health Check:** Tests connectivity against the `/v1/models` endpoint and verifies model catalog availability.
- **Live Smoke Test:** Run `ALLOW_LIVE_SMOKE_TESTS=true NEBIUS_API_KEY=sk-... pytest backend/tests/unit/test_nebius_cloud.py` to verify real cloud inference.

---

## 5. Local LLM: Ollama (`qwen3.5:9b`)

To run entirely locally with open-weights LLMs:

1. Install [Ollama](https://ollama.ai/) and start the daemon.
2. Pull the designated model:
   ```powershell
   ollama pull qwen3.5:9b
   ```
3. Set your `.env`:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=qwen3.5:9b
   ```
4. Verify via health check: `GET http://localhost:8000/api/v1/health`

---

## 6. Live Web Search: Tavily Integration

When live web search is desired:
1. Obtain an API key from [Tavily](https://tavily.com/).
2. In `.env`, set:
   ```env
   TAVILY_API_KEY=tvly-your-actual-api-key
   ```
3. In the UI, the search mode toggle will allow selecting **"Live Tavily Search"**.
4. **Zero Silent Fallbacks:** If a live search request fails (e.g. rate limit, bad network), Sentinel displays an explicit error alert with a retry button. It **never** silently substitutes fake fixture data in live mode.

---

## 7. Evaluation Benchmark & Results

Sentinel includes an automated evaluation benchmark comparing **SupplyChain Sentinel** against a **Baseline LLM Approach** across 8 versioned, realistic edge cases.

### Benchmark Edge Cases (`evaluation/benchmark_dataset_v1.json`)
- **CASE-01:** Genuine Critical Disruption with Syndicated News Wires (Apex Semiconductor factory fire).
- **CASE-02:** Irrelevant Incident at Non-Critical Facility (Titan Energy substation blast).
- **CASE-03:** Entity Disambiguation on Similar-Name Company (Australian packaging firm vs UK fastener supplier).
- **CASE-04:** Wire Duplication Without Corroboration (3 copies of single port strike report).
- **CASE-05:** Corrected Drill Report / Exercise (Hydraulic drill false alarm).
- **CASE-06:** Unverified Social Media Rumor (Uncorroborated forum rumor).
- **CASE-07:** Missing Inventory and Recovery Data (Null-safety test).
- **CASE-08:** Irrelevant Technical Whitepaper (Ungrounded industry report).

### Benchmark Results (`evaluation/evaluation_results.json`)

| Metric | Mathematical Denominator | SupplyChain Sentinel | Baseline LLM | Description |
|---|---|:---:|:---:|---|
| **Supplier Attribution Accuracy** | 9 total benchmark cases | **100.0%** | 88.9% | Correct corporate entity resolution vs naive name matching |
| **Supporting Quote Validity** | 9 total extracted claims | **100.0%** | 88.9% | Mathematically verified exact substring matches against source |
| **Duplicate Wire Handling** | 2 syndicated wire cases | **100.0%** | 0.0% | Correct clustering of syndicated news wires preventing false corroboration |
| **False Escalation Rate** | 8 non-escalatable cases | **0.0%** | 87.5% | Non-critical, irrelevant, or misattributed cases wrongly escalated |
| **Critical Incident Recall** | 1 genuine critical case | **100.0%** | 100.0% | Recall of genuine critical disruptions requiring procurement intervention |
| **Uncertainty Handling Precision** | 2 missing/ambiguous data cases | **100.0%** | 0.0% | Correct refusal to invent inventory numbers or hallucinate risk |

> **Hackathon Submission Package:** For the complete 3-minute video demo script, storyboard, and developer feedback on Nebius Token Factory and NVIDIA models, see [`docs/SUBMISSION.md`](docs/SUBMISSION.md).

### Reproducing the Benchmark
Run the standalone runner script:
```powershell
.\backend\.venv\Scripts\python.exe evaluation\runner.py
```
Or run the automated pytest test:
```powershell
.\backend\.venv\Scripts\pytest backend\tests\unit\test_evaluation_benchmark.py -v
```

---

## 8. Verification & Quality Gates

Run all automated quality gates across backend and frontend:

```powershell
# 1. Run all backend unit tests (95 passing tests)
.\backend\.venv\Scripts\pytest -k "not test_live_ollama"

# 2. Run Ruff lint check
.\backend\.venv\Scripts\ruff check backend evaluation

# 3. Run Ruff formatting check
.\backend\.venv\Scripts\ruff format --check backend evaluation

# 4. Run Frontend TypeScript check
npm --prefix frontend run typecheck

# 5. Run Frontend production build
npm --prefix frontend run build
```

---

## 9. Known Limitations & Edge Cases

1. **Entity Name Disambiguation Heuristics:** The current entity resolution module checks normalized legal names, aliases, corporate domains, and country locations. Complex multinational corporate ownership structures (e.g. holding companies with multi-tier subsidiaries) require enterprise ERP integration.
2. **Deterministic Search Queries:** Live search queries are structured deterministically (`"{supplier_name} {part_name} disruption fire strike delay"`). Complex multi-hop Boolean searches are outside current scope.
3. **Database Concurrency:** SQLite with WAL mode is used for simple zero-dependency local demonstration. For production enterprise deployment with dozens of concurrent procurement reviewers, PostgreSQL is recommended.
4. **Live Cloud API Verification:** While all adapter contracts, auth errors, 429 quota handling, and schema fallback logic are 100% covered by unit tests, live Nebius Token Factory inference requires the operator to provide their own active `NEBIUS_API_KEY`.

---

## 10. License

MIT License — see [LICENSE](LICENSE) for details.
