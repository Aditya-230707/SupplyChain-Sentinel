# SupplyChain Sentinel — Hackathon Submission Package
> **Hackathon:** Nebius × NVIDIA Global AI Hackathon 2026  
> **Repository:** [https://github.com/Aditya-230707/SupplyChain-Sentinel](https://github.com/Aditya-230707/SupplyChain-Sentinel)  
> **License:** MIT License ([LICENSE](LICENSE))

---

## 1. Project Overview & Architecture

### The Problem
Procurement and risk intelligence teams monitoring global supply chains face an influx of breaking news, wire alerts, and social media chatter. Applying raw generative LLMs directly to this problem leads to dangerous failure modes:
1. **Hallucinated Citations:** LLMs fabricate or paraphrase quotes that do not exist verbatim in the source.
2. **Duplicate Wire False Corroboration:** Reprints of the same AP or Reuters wire across 10 aggregator websites are mistaken by LLMs for 10 independent confirmations.
3. **Entity Conflation:** A cyberattack at a retail packaging company named "Vertex Ltd" in Australia causes an LLM to recommend halting orders to "Vertex Components Ltd", an aerospace fastener supplier in the UK.
4. **Premature Autonomous Actions:** LLMs panic on sensational words ("explosion", "fire") and recommend freezing purchase orders even when the factory line is explicitly unaffected or inventory coverage is unknown.

### The Solution: SupplyChain Sentinel
SupplyChain Sentinel implements an **evidence-first, deterministic intelligence architecture** where LLMs are restricted strictly to structured extraction, while all verification, exposure calculations, and business policy decisions are governed by deterministic, testable Python algorithms.

```
[Public Reports / Web Wires] ───► [Search Provider (Fixture or Tavily)]
                                             │
                                             ▼
                                  [Source Normalizer]
                               (Canonical URL + SHA-256)
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
                           (Exact Substring Quote Verification)
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

---

## 2. Nebius Token Factory & NVIDIA Model Integration

SupplyChain Sentinel is engineered with a clean provider abstraction (`app/providers/llm_base.py`) supporting:
1. **Nebius Token Factory Cloud Path:** Connects to `https://api.tokenfactory.nebius.com/v1/` using NVIDIA foundation models (`nvidia/Nemotron-3_5-Lightning`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b`).
2. **Deterministic Offline Path:** Zero-network fake provider (`FakeLLMProvider`) for deterministic testing and automated evaluation.

### Cloud Architecture & Resilience Features
- **Key Redaction:** `NebiusTokenFactoryProvider` explicitly redacts API credentials from all exception strings and health check responses.
- **Reasoning Control:** NVIDIA Nemotron defaults to internal reasoning tokens (`enable_thinking: true`) which can consume token budgets before schema emission; the provider passes `chat_template_kwargs: {"enable_thinking": False}` to ensure immediate, deterministic JSON generation.
- **Structured Schema Resilience:** Attempts strict `json_schema` mode first, automatically falling back to `json_object` mode if an endpoint lacks schema enforcement.
- **Catalog Verification:** Health check dynamically queries `/v1/models` to verify model catalog availability.
- **Provider Status:** 100% of adapter contracts, 401 auth errors, 429 rate limit exceptions, and schema fallbacks are validated via unit tests in `tests/unit/test_nebius_cloud.py`. Live inference with `nvidia/Nemotron-3_5-Lightning` has been verified end-to-end via single-request smoke testing and bounded orchestrator pipeline execution.

---

## 3. Evaluation Benchmark Results

We audited the system using an automated 20-case synthetic benchmark dataset (`evaluation/benchmark_dataset_v1.json` & `evaluation/runner.py`) comparing SupplyChain Sentinel against a curated deterministic Baseline LLM across explicit mathematical denominators and dynamic flags (detailed in `docs/METRIC_DEFINITIONS.md`):

| Metric | Mathematical Denominator | Baseline LLM | Sentinel 1-Shot | Sentinel + VOI Loop | Guarantee |
|---|---|:---:|:---:|:---:|---|
| **Supplier Attribution Accuracy** | 20 total benchmark cases | 85.0% | **95.0%** | **95.0%** | Multi-signal entity & facility resolution vs naive keyword matching |
| **Supporting Quote Validity** | 20 total extracted claims | 90.0% | **100.0%** | **100.0%** | Rule E-005 exact substring check eliminates quote fabrication |
| **Duplicate Wire Handling** | 2 syndicated wire cases | 0.0% | **100.0%** | **100.0%** | Content hashing clusters wire reprints to prevent false corroboration |
| **False Escalation Rate** | 17 non-critical cases | 94.1% | **0.0%** | **0.0%** | Deterministic policy rulebook eliminates premature panic freezes |
| **Critical Incident Recall** | 3 genuine critical cases | 100.0% | **100.0%** | **100.0%** | 100% recall on genuine critical disruptions requiring action |
| **Uncertainty Handling Precision** | 3 missing/ambiguous cases | 0.0% | **100.0%** | **100.0%** | Missing data remains null; refuses to invent inventory numbers |
| **VOI Decision Change Efficiency** | 2 unresolved gap cases | 0.0% | 0.0% | **100.0%** | Directional accuracy and information gain from follow-up inquiries |

*Reproduction:* Run `python evaluation/runner.py` or `pytest backend/tests/unit/test_evaluation_benchmark.py`. See complete mathematical definitions in `docs/METRIC_DEFINITIONS.md`.

---

## 4. 3-Minute Video Demo Script & Storyboard

### Video Target Duration: 2 minutes 50 seconds (< 3 minutes)

| Timestamp | Screen / Visual | Voiceover Audio Script | Key Differentiation Shown |
|---|---|---|---|
| **0:00 – 0:25** | Sentinel UI Dashboard & Architecture Diagram | *"Welcome to SupplyChain Sentinel. When news breaks of a factory fire or port strike, enterprise procurement teams cannot afford to rely on generative AI alone. Ungrounded LLMs hallucinate quotes, confuse distinct companies with similar names, treat wire reprints as multiple confirmations, and recommend premature order freezes. Sentinel fixes this with an evidence-first, deterministic intelligence pipeline."* | Clear problem statement: Enterprise risk of ungrounded LLM decisions. |
| **0:25 – 1:05** | **Demo 1: Genuine Critical Disruption** (Silicon Foundry Dresden) | *"Let's test Scenario 1: Silicon Foundry Dresden GmbH. Three news outlets reported on a cleanroom fire. Notice how Sentinel's Lineage Analyzer immediately groups the Reuters and TechWires reports into a single wire syndication family, preventing artificial corroboration. Look at the supporting quotation: it is highlighted in green, mathematically verified as an exact substring. Based on the supplier's 14 days of inventory versus 45 days of downtime, Sentinel deterministically calculates a 31-day inventory gap and triggers urgent human review."* | Syndicated wire clustering, Rule E-005 quote validation, exact mathematical inventory gap calculation. |
| **1:05 – 1:40** | **Demo 2: True Incident, Irrelevant Facility** (Titan Energy Solutions) | *"Now let's switch to Scenario 2: Titan Energy Solutions. A transformer explosion occurred at a utility substation in Houston. A raw LLM panics on the word 'explosion' and recommends freezing orders. But Sentinel inspects the verified quote: 'Central battery pack manufacturing facilities were unaffected.' Rule P-007 fires, deterministically recommending 'Monitor' rather than freezing supply."* | Elimination of false escalation on non-critical facilities. |
| **1:40 – 2:15** | **Demo 3: Entity Disambiguation** (Vertex Components Ltd) | *"Scenario 3: Breaking news reports that 'Vertex Ltd' suspended operations after a cyberattack. A naive AI immediately links this to our UK aerospace fastener supplier. But Sentinel's multi-signal entity resolver detects that the reported company is in Melbourne, Australia and manufactures retail packaging. Because identity signals contradict, Rule P-001 fires, blocking high-consequence action and outputting 'Insufficient Evidence'."* | Multi-signal entity resolution prevents cross-company confusion. |
| **2:15 – 2:40** | **Human Decision Gate & Audit Trail** | *"Sentinel never executes autonomous order cancellations. Here in the Human Review Gate, procurement managers inspect the evidence, review policy rationales, and record decisions. I can accept the recommendation or override it. If I override, Sentinel requires a mandatory justification note, creating a permanent, immutable audit trail."* | Human-in-the-loop governance and immutable audit trail. |
| **2:40 – 2:55** | Nebius Cloud Architecture & Conclusion | *"Behind the scenes, Sentinel integrates with Nebius Token Factory running NVIDIA Nemotron foundation models, backed by deterministic rulebooks. SupplyChain Sentinel: verifiable, safe, evidence-first AI for global supply chains. Thank you."* | Nebius Token Factory & NVIDIA open model integration. |

---

## 5. Feedback on Nebius Token Factory & NVIDIA Tooling

Based on our implementation and architectural integration of Nebius Token Factory:

### Strengths
1. **Frictionless OpenAI-Compatible Protocol:** The standard `/v1/chat/completions` and `/v1/models` endpoints allowed using the standard `AsyncOpenAI` SDK without custom proprietary client libraries.
2. **NVIDIA Nemotron Open Weights Support:** Availability of high-performing open models like `nvidia/Nemotron-3_5-Lightning` provides strong reasoning capabilities with competitive latency.
3. **Structured Output Handling:** Clean response formatting when using `json_object` and `json_schema` configurations.

### Opportunities for Improvement
1. **Catalog Visibility & Consistency:** Model IDs occasionally vary across console documentation versus `/v1/models` catalog listings. Standardizing naming aliases (e.g., `nvidia/nemotron-3-super` vs `nvidia/Nemotron-3-Super`) would streamline deployment.
2. **Rate Limit Headers:** Standardizing HTTP 429 response bodies with explicit `retry-after` seconds in header payloads would enhance automated exponential backoff implementations.
3. **Interactive Playground Schema Tester:** A built-in JSON schema validator in the Nebius Token Factory console would accelerate prompt engineering for structured extraction pipelines.

---

## 6. Prior Work & Attribution

- **Original Hackathon Implementation:** All core pipeline code (lineage clustering, exact quote substring validation, multi-signal entity resolution, deterministic policy rulebook, and human review gate) was designed and implemented during the hackathon following the provided engineering blueprint.
- **Open Source Foundations:** Built using standard open-source libraries: FastAPI (backend API), React/Vite (frontend UI), Pydantic v2 (schema validation), SQLAlchemy 2.x/aiosqlite (persistence), and Lucide React (icons).

---

## 7. Known Limitations & Production Roadmap

1. **Enterprise ERP Sync:** Currently uses explicit supplier profile records and inventory coverage days. Production deployments would synchronize real-time ERP inventory via SAP or Oracle APIs.
2. **Global Corporate Registry Lookups:** The multi-signal entity resolver utilizes legal names, aliases, domains, and country filters. Integration with authoritative global corporate databases (e.g., Dun & Bradstreet, OpenCorporates) would further strengthen international entity matching.
3. **Database Scale:** Built on SQLite with WAL mode for zero-dependency local demonstration. Production enterprise multi-user deployment recommends PostgreSQL with read replicas.

---

## 8. Submission Status & Pending Deliverables

| Deliverable | Requirement | Status | Notes |
|---|---|:---:|---|
| **Public GitHub Repository** | Complete codebase, documentation, tests | **READY** | All code hardened, 137 unit tests passing |
| **Open Source License** | Permissive open source license | **VERIFIED** | MIT License in root (`LICENSE`) |
| **Reproducible Local Setup** | Zero external API key quickstart | **VERIFIED** | Unified hosting on port 8000 (`make host`) |
| **Nebius & NVIDIA Integration** | Live cloud inference & reasoning control | **VERIFIED** | NVIDIA Nemotron-3_5-Lightning verified live |
| **Benchmark & Validation** | 20-case synthetic benchmark & 12-stage E2E trace | **VERIFIED** | 20/20 benchmark passing, E2E trace green |
| **Demo Video (< 3 minutes)** | Video walkthrough demonstrating core scenarios | **PENDING** | Storyboard & verbatim audio script ready in Section 4 |
| **Devpost Submission** | Project write-up, team, and video link | **PENDING** | Awaiting video URL and portal form submission |
