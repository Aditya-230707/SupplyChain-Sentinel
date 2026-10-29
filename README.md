# SupplyChain Sentinel — Autonomous Risk Intelligence

> **Evidence-First Supplier Incident Intelligence**  
> Built for the *Nebius × NVIDIA Global AI Hackathon 2026*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-green.svg)](https://www.python.org/)
[![React: 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Evaluation: 100% Quote Validity](https://img.shields.io/badge/Quote_Validity-100%25-brightgreen.svg)](evaluation/evaluation_results.json)
[![Evaluation: 0% False Escalation](https://img.shields.io/badge/False_Escalation-0.0%25-brightgreen.svg)](evaluation/evaluation_results.json)
[![Evaluation: 100% VOI Efficiency](https://img.shields.io/badge/VOI_Efficiency-100%25-brightgreen.svg)](evaluation/evaluation_results.json)

---

## 1. What SupplyChain Sentinel Does
Enterprise supply chain teams are bombarded by breaking news, wire alerts, and social media rumors regarding factory fires, port strikes, and cyberattacks. Generative AI alone frequently hallucinates quotes, conflates same-name companies, treats duplicate syndicated wire releases as independent corroboration, and recommends premature order freezes.

**SupplyChain Sentinel** is a deterministic, evidence-grounded decision intelligence platform:
1. **Never trusts raw LLM output:** Model extraction is strictly parsed via typed Pydantic schemas.
2. **Deterministic quote validation (Rule E-005):** Every supporting quote extracted by an LLM is mathematically verified as an exact substring against the immutable retrieved source text.
3. **Syndicated wire lineage clustering (Rules E-001 to E-003):** Automatically groups syndicated press releases and wire copies (via URL canonicalization and SHA-256 fingerprinting) so duplicate reporting does not falsely inflate corroboration confidence.
4. **Multi-signal corporate & facility entity resolution (ID-001 to ID-005, FAC-001):** Resolves legal entity names, stock tickers, corporate domains, and specific manufacturing facilities against buyer contracts to prevent false alerts.
5. **Evidence graph provenance DAG:** Connects all sources, claims, facilities, parts, exposure calculations, and policy decisions into an inspectable bipartite Directed Acyclic Graph with explicit semantic relations (`CORROBORATES`, `CONTRADICTS`, `ECHOES`).
6. **Mathematical exposure & decision loss engine (EX-001 to EX-009):** Propagates duration ranges $[D_{\min}, D_{\max}] \to [\text{gap}_{\min}, \text{gap}_{\max}]$ with strict null safety, models deterministic scenarios (Short, Baseline, Extended), and calculates expected decision loss $\mathbb{E}[L(a)]$.
7. **Bounded Next-Best-Investigation loop (VOI-001 to VOI-004):** Automatically identifies unresolved evidentiary gaps, ranks targeted research queries using a transparent Value of Information (VOI) heuristic, executes bounded follow-ups, and records full decision traces.
8. **Explicit policy rulebook (P-001 to P-010):** Action recommendations (`urgent_human_review`, `review_contingency_plan`, `request_supplier_confirmation`, `monitor`, `insufficient_evidence`) are produced exclusively by deterministic Python code, never by free-form LLM generation.
9. **Human-in-the-loop decision gate:** The system never autonomously halts orders or cancels contracts. Procurement managers inspect evidence, audit source lineage, and record decisions with full historical audit trails.

---

## 2. Architecture & Pipeline

```text
[Public News / Reports] ───► [Search Provider (DuckDuckGo / Tavily / Fixture)]
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
                    (Nebius Token Factory / NVIDIA Nemotron)
                                         │
                                         ▼
                        [Deterministic Claim Validator]
                       (Substring Quote Verification)
                                         │
                                         ▼
                        [Entity & Facility Resolver]
                    (Domain, Registry, Country, Cleanroom Plant)
                                         │
                                         ▼
                         [Semantic Claim Relations]
                   (Contradiction, Corroboration, Wire Echo)
                                         │
                                         ▼
                      [Mathematical Exposure & Loss Engine]
                  (Range Propagation, Scenarios, Expected Loss)
                                         │
                                         ▼
                       [Deterministic Policy Rulebook]
                          (Rules P-001 through P-010)
                                         │
                                         ▼
                     [Bounded Next-Best-Investigation (VOI)]
                   (Gaps Identification ──► VOI Query Execution)
                                         │
                                         ▼
                       [Evidence Graph Provenance DAG]
                       (Audit Ledger & Bipartite Graph)
                                         │
                                         ▼
                      [Human Reviewer Decision Gate & Audit]
```

### Deterministic Principles
- **E-005 (Quote Integrity):** Any claim whose quote is not found verbatim in the source text is marked `quote_mismatch` and rejected.
- **ID-001 to ID-004 (Entity Disambiguation):** Ambiguous corporate names or location contradictions block high-impact escalation and trigger `request_supplier_confirmation`.
- **FAC-001 (Facility Mismatch):** Incidents at facilities not used by the buyer are categorized as non-impacting.
- **EX-002 & EX-007 (Range & Null Safety):** If duration or inventory days are unknown, gap is strictly `None`. When intervals $[D_{\min}, D_{\max}]$ are cited, range bounds propagate without distortion.
- **P-001 to P-010 (Policy Gate):** Single uncorroborated reports never trigger emergency order freezes; resolved/drill events trigger `monitor`.
- **VOI-001 to VOI-004 (Next-Best Investigation):** Resolves missing recovery timelines or unverified single sources via bounded follow-up inquiries.

---

## 3. Quick Start & Unified Hosting (Zero API Keys)

You can run and test SupplyChain Sentinel immediately with zero external API dependencies or cloud accounts.

### Prerequisites
- Python 3.12 or 3.13
- Node.js 18+ and npm
- Git

---

### Option A: Unified Single-Port Hosting (Recommended)
FastAPI directly serves the production React SPA bundle alongside all REST APIs and OpenAPI documentation on a single port (`8000`):

```powershell
# 1. Clone repository
git clone https://github.com/Aditya-230707/SupplyChain-Sentinel.git
cd SupplyChain-Sentinel
copy .env.example .env

# 2. Build frontend and host unified application
make host
```
*(Or manually without make:)*
```powershell
npm --prefix frontend run build
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```

- **Live Web Interface:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Health Diagnostics:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option B: Containerized Hosting (Docker & Docker Compose)
```bash
# Build and run with persistent database volume:
docker compose up -d --build
```
Open [http://localhost:8000/](http://localhost:8000/) in your browser.

---

### Option C: Local Development Mode (Hot Reloading)

```powershell
# Terminal 1: Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd ..\frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:5173`

---

### Step 4: Run an Investigation
1. In the UI, navigate to **Investigations** and click **"+ Start Investigation"** (or choose any registered supplier).
2. Choose search mode: **DuckDuckGo Live** (real web search, no keys required), **Tavily Live**, or **Deterministic Fixture**.
3. Use the **Sample Scenario** dropdown to pre-fill test cases (**Silicon Foundry Dresden GmbH**, **Titan Energy Solutions**, or **Vertex Components Ltd**).
4. Inspect the verified claims, verbatim quote validation (Rule E-005), and deterministic operational exposure calculation.
5. In the **Human Review Gate**, select "Accept Recommendation" or "Override", provide rationale, and click **"Record Decision & Sign Off"**.
6. Check the persistent **Audit Trail** for the immutable event record.

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
- **Key Redaction:** The API key is stored strictly in memory, never logged, and explicitly stripped from structured logging and error messages.
- **Thinking Mode Control:** Enforces `chat_template_kwargs={"enable_thinking": False}` for clean, latency-optimized structured extraction with `nvidia/Nemotron-3_5-Lightning`.
- **Structured Output Resilience:** Uses OpenAI-compatible client with `response_format={"type": "json_object"}` and strict Pydantic model validation.
- **Production Guard:** `APP_ENV=production` automatically enforces `LLM_PROVIDER=nebius` and fails fast if credentials or models are missing.
- **Provider Health Check:** Tests connectivity against the `/v1/models` endpoint and verifies model catalog availability.
- **Live Cloud Smoke Test:** Set `ALLOW_LIVE_SMOKE_TESTS=true` and valid `NEBIUS_API_KEY` in `.env`, then run `pytest backend/tests/unit/test_nebius_cloud.py`.

---

## 5. Offline Testing: Deterministic Provider (`fake`)

For automated CI/CD and zero-dependency local testing without cloud credentials:

1. Set your `.env`:
   ```env
   LLM_PROVIDER=fake
   ```
2. The zero-network `FakeLLMProvider` deterministically simulates structured extraction for offline test suites, contract validation, and range-propagation benchmarks without incurring cloud API calls or network latency.
3. For live incident intelligence and hackathon evaluation, set `LLM_PROVIDER=nebius` with your Nebius Token Factory credentials.

---

## 6. Live Web Search: DuckDuckGo & Tavily Integrations

### A. DuckDuckGo Live Search (Zero API Keys Required)
By default, Sentinel queries real-time public web news and incident wires via DuckDuckGo without requiring external API keys:
- Extracts live publisher metadata, publication timestamps, and source URLs.
- Fetches and parses target article HTML with `beautifulsoup4` and `httpx`.
- Built-in SSRF protection prevents network traversal into private IP ranges.

### B. Tavily Live Search (API Key Integration)
For enterprise-grade curated search feeds:
1. In `.env`, set `TAVILY_API_KEY=tvly-your-actual-api-key`.
2. In the UI, select **"Tavily Live Search"**.
3. **Zero Silent Fallbacks:** If a live search fails, Sentinel displays an explicit error alert with a retry option. It **never** silently substitutes simulated fixture data during live investigations.

---

## 7. Evaluation Benchmark: 3-Way Comparative Results

Sentinel features a 20-case versioned challenge benchmark dataset ([`evaluation/benchmark_dataset_v1.json`](evaluation/benchmark_dataset_v1.json)) and runner ([`evaluation/runner.py`](evaluation/runner.py)) evaluating 3 distinct paradigms across boundary failure modes:
1. **Reference Baseline:** Fixed reference simulation capturing typical failure modes of raw ungrounded LLMs (lack of wire deduplication, premature panic on negative keywords, quote hallucination).
2. **SupplyChain Sentinel (1-Shot Deterministic):** Exact quote validation, lineage clustering, entity/facility resolution, range exposure math, and policy rulebook.
3. **SupplyChain Sentinel + Bounded Next-Best-Investigation (VOI):** Bounded inquiry loop that closes evidence gaps, quantifies missing durations, and resolves unverified single sources.

> **Evaluation Methodology & Limitations:** These 20 cases are curated, deterministic challenge scenarios designed to test specific edge-case rules (e.g., exact quote substring matching, corporate homonyms, non-impacting facility damage). Sub-denominators for specific flags reflect targeted boundary tests (e.g., $N=2$ for wire deduplication, $N=3$ for critical incidents, $N=2$ for VOI gap resolution) rather than general statistical sampling across all supply chains. See [`docs/METRIC_DEFINITIONS.md`](docs/METRIC_DEFINITIONS.md) for full mathematical definitions and disclaimers.

### Benchmark Results (`evaluation/evaluation_results.json`)

| Metric | Eligible Denominator | Reference Baseline | Sentinel 1-Shot | Sentinel + VOI Loop | Target Algorithmic Guarantee |
|---|---|:---:|:---:|:---:|---|
| **Supplier Attribution Accuracy** | $N=20$ benchmark cases | 85.0% | **95.0%** | **95.0%** | Multi-signal entity & facility resolution vs naive keyword matching |
| **Supporting Quote Validity** | $N=20$ extracted claims | 90.0% | **100.0%** | **100.0%** | Mathematically verified exact substring matches against source |
| **Duplicate Wire Handling** | $N=2$ syndicated wire cases | 0.0% | **100.0%** | **100.0%** | Accurate clustering of syndicated news wires preventing inflated confidence |
| **False Escalation Rate** | $N=17$ non-escalatable cases | 94.1% | **0.0%** | **0.0%** | Non-critical, irrelevant, or misattributed cases wrongly escalated |
| **Critical Incident Recall** | $N=3$ genuine critical cases | 100.0% | **100.0%** | **100.0%** | Recall of genuine critical disruptions requiring procurement intervention |
| **Uncertainty Handling Precision** | $N=3$ missing/ambiguous data cases | 0.0% | **100.0%** | **100.0%** | Correct preservation of nulls and refusal to hallucinate risk |
| **VOI Decision Change Efficiency** | $N=2$ unresolved gap cases | 0.0% | 0.0% | **100.0%** | Directional accuracy and information gain achieved by targeted follow-up inquiries |

### Reproducing the Benchmark
Run the standalone 3-way evaluation runner:
```powershell
.\backend\.venv\Scripts\python.exe evaluation\runner.py
```
Or run the automated unit test:
```powershell
.\backend\.venv\Scripts\pytest backend\tests\unit\test_evaluation_benchmark.py -v
```

---

## 8. Verification & Quality Gates

Run all automated quality gates across backend and frontend:

```powershell
# 1. Run all backend unit tests (145 passing tests, 1 skipped)
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/unit -m "not slow" -q

# 2. Run Ruff lint check (clean across all files)
.\backend\.venv\Scripts\python.exe -m ruff check backend evaluation

# 3. Run Ruff formatting check
.\backend\.venv\Scripts\python.exe -m ruff format --check backend evaluation

# 4. Run Frontend ESLint check (0 warnings, 0 errors)
npm --prefix frontend run lint

# 5. Run Frontend TypeScript typecheck
npm --prefix frontend run typecheck

# 6. Run Frontend production build
npm --prefix frontend run build

# 7. Run 12-stage offline E2E pipeline verification
.\backend\.venv\Scripts\python.exe backend/scripts/validate_e2e_investigation.py

# 8. Run 3-way comparative benchmark suite
.\backend\.venv\Scripts\python.exe evaluation/runner.py
```

---

## 9. Known Scope & Operational Limitations

1. **Curated Benchmark Scope:** Evaluated on 20 edge-case boundary scenarios. While rigorous for testing rule triggers and quote integrity, it does not represent an empirical survey of global news corpora.
2. **Public News Visibility:** Relies on indexed public news and statements via DuckDuckGo and Tavily. Proprietary tier-2/tier-3 sub-tier disruptions not reported in public media require internal buyer notifications.
3. **Enterprise ERP Sync:** Current master data uses local relational records. Live enterprise production requires bidirectional integration with SAP S/4HANA or Oracle Cloud SCM.
4. **Heuristic Lineage Clustering:** Lineage clustering groups canonical URLs, content hashes, and syndicated wire citations. Highly paraphrased or completely rewritten derivative reporting without wire citations may evade heuristic detection.
5. **Human-in-the-Loop Requirement:** Consequential procurement decisions (order redirection, dual-sourcing invocation) require human review through the Decision Gate.

---

## 10. Hackathon Submission Package

For complete details on the architecture, developer feedback on Nebius Token Factory and NVIDIA models, and video demonstration storyboards, see [`docs/SUBMISSION.md`](docs/SUBMISSION.md).

*(Note: The demonstration video is recorded and linked directly on the Devpost submission page).*

---

## 11. License

MIT License — see [LICENSE](LICENSE) for details.
