# SupplyChain Sentinel — Comprehensive User Manual & Operations Guide

> **System Version:** 0.1.0-release  
> **LLM Cloud Provider:** Nebius Token Factory  
> **Foundation Model:** `nvidia/Nemotron-3_5-Lightning` (NVIDIA Open-Weights Inference)  
> **Web Interface:** Unified Single-Port Hosting on `http://localhost:8000/`  
> **Interactive API Documentation:** `http://localhost:8000/api/docs`  

---

## Table of Contents

1. [Executive Overview & Purpose](#1-executive-overview--purpose)
2. [How SupplyChain Sentinel Works](#2-how-supplychain-sentinel-works)
3. [Quick Start: Hosting & Accessing the System](#3-quick-start-hosting--accessing-the-system)
4. [Step-by-Step User Walkthrough](#4-step-by-step-user-walkthrough)
   - [Step 1: Dashboard & Active Monitoring](#step-1-dashboard--active-monitoring)
   - [Step 2: Creating a New Investigation](#step-2-creating-a-new-investigation)
   - [Step 3: The Multi-Stage Verification Pipeline](#step-3-the-multi-stage-verification-pipeline)
   - [Step 4: Forensic Workspace & Evidence Inspection](#step-4-forensic-workspace--evidence-inspection)
   - [Step 5: Human-in-the-Loop Decision Gate](#step-5-human-in-the-loop-decision-gate)
   - [Step 6: Suppliers Management & Inventory Buffer](#step-6-suppliers-management--inventory-buffer)
   - [Step 7: Immutable Audit Trail](#step-7-immutable-audit-trail)
5. [The Three Benchmark Challenge Scenarios](#5-the-three-benchmark-challenge-scenarios)
6. [System Diagnostics & Operator Verification](#6-system-diagnostics--operator-verification)
7. [Programmatic REST API Guide](#7-programmatic-rest-api-guide)
8. [Troubleshooting & Common Questions](#8-troubleshooting--common-questions)

---

## 1. Executive Overview & Purpose

**SupplyChain Sentinel** is an evidence-first, deterministic intelligence system designed to protect global supply chains from costly false alarms and undetected vendor disruptions. 

### The Problem with Traditional GenAI in Supply Chains:
- **Panic on Negative Keywords:** Standard LLMs read words like *"fire"*, *"substation explosion"*, or *"cyberattack"* and prematurely recommend multi-million dollar expedited orders or order cancellations, even if the event occurred at an unrelated facility.
- **Wire Echo Inflation:** A single syndicated Reuters or Bloomberg wire reprinted across 20 web portals is counted as 20 independent confirmations by naive algorithms.
- **Quote Hallucination:** Generative models frequently summarize or rephrase statements, introducing claims never actually made by facility operators or fire chiefs.
- **Corporate Homonym Confusion:** Two companies sharing the same name in different countries (e.g. *Vertex Components Ltd* in the UK vs *Vertex Ltd* in Australia) are mistakenly merged.

### The Sentinel Solution:
SupplyChain Sentinel pairs high-throughput cloud inference on **Nebius Token Factory** (`nvidia/Nemotron-3_5-Lightning`) with a **strictly deterministic mathematical rulebook**. Every claim extracted by the model must be anchored to an exact character substring in the primary source, validated against syndicated wire lineage, entity-disambiguated, and balanced against your company's actual inventory buffer days.

---

## 2. How SupplyChain Sentinel Works

```
                        [ Public Web / News Wires ]
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  1. Search & Ingestion Adapter  │
                    │   • DuckDuckGo Live / Tavily    │
                    │   • SSRF Safe Proxy & DNS Guard │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  2. Syndicated Lineage Engine   │
                    │   • Canonical URL normalization │
                    │   • Wire By-Line Deduplication  │
                    │   • SimHash / Content Cluster   │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  3. Nebius Token Factory Cloud  │
                    │   • NVIDIA Nemotron-3.5-Lightn. │
                    │   • Structured Incident Claims  │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
     ┌───────────────────────────────────────────────────────────────┐
     │            4. Deterministic Verification Rulebook             │
     │  • Rule E-005: Exact Substring Quote Matching                 │
     │  • Rules ID-001–005: Multi-Signal Entity Resolution           │
     │  • Rules CR-001: Claim-to-Claim Contradiction Detection       │
     │  • Rule E-001: Independent Source Group Counting              │
     └───────────────────────────────┬───────────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  5. Bounded Exposure Arithmetic │
                    │   Operational Gap = Recovery    │
                    │      Days - Inventory Buffer    │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  6. Human-in-the-Loop Decision  │
                    │   • Approve / Override / Dismiss│
                    │   • Immutable Audit Ledger      │
                    └─────────────────────────────────┘
```

---

## 3. Quick Start: Hosting & Accessing the System

SupplyChain Sentinel uses a **unified single-port architecture**: FastAPI hosts both the production React SPA and the high-speed REST endpoints on port `8000`.

### Starting the Server
Run the following command from the repository root:
```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
*(Or on Linux/macOS: `make host`)*

### Access Points:
- **Web Application:** [http://localhost:8000/](http://localhost:8000/)
- **Built-in User Manual:** [http://localhost:8000/](http://localhost:8000/) (Click **User Manual** on the left sidebar)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Health Diagnostics:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Cloud Provider Health:** [http://localhost:8000/api/v1/health/providers](http://localhost:8000/api/v1/health/providers)

---

## 4. Step-by-Step User Walkthrough

### Step 1: Dashboard & Active Monitoring
When you open [http://localhost:8000/](http://localhost:8000/), you land on the **Investigations Dashboard**:
1. The sidebar displays real-time badges of past investigations, tracked suppliers, and audit log entries.
2. The footer shows live inference status (`nvidia/Nemotron-3_5-Lightning` via Nebius Token Factory).
3. The main panel displays all investigation runs with their status (`completed`, `extracting`, `queued`), severity rating, and timestamp.

### Step 2: Creating a New Investigation
Click the **`+ New Investigation`** button in the sidebar or top bar to open the **New Supplier Investigation** screen:

* **Top Right — Sample Scenario Dropdown:**  
  Use the dropdown **`Sample Scenario: [ Select scenario to pre-fill… ]`** to automatically load one of the 3 benchmark edge cases (*Cleanroom Fire*, *Substation Incident*, or *Cyber Alert*). It pre-fills all fields and selects *Deterministic Fixtures* so you can evaluate the pipeline with one click.

* **1. Search & Discovery Engine:**
  - **DuckDuckGo Live (Checked by default):** Zero-API-key live web search with automated SSRF protection.
  - **Deterministic Fixtures:** Offline challenge scenarios for instant reproducible evaluation.
  - **Tavily Search:** Commercial syndicated wire search (requires `TAVILY_API_KEY`).

* **2. Target Supplier:**
  - Click **`[Select Existing (26)]`** to choose a vendor already tracked in your database.
  - Or click **`[Enter Details]`** to type custom parameters: *Supplier Legal Name \**, *Country / Jurisdiction*, *Official Domain* (for entity resolution), and *Criticality Tier* (Tier 1 High, Tier 2 Medium, Tier 3 Low).

* **3. Operational Exposure Context (Optional) — Formula EX-003:**
  Calculates exposure via: `Gap = max(0, Disruption Duration − Safety Stock)`.
  - **Critical Component / Part Name:** (e.g. `Automotive Microcontroller MCU-4`).
  - **Safety Stock Coverage (Days):** (e.g. `14`). The buffer stock available at your plants.
  - **Estimated Disruption (Days):** (e.g. `45`). The reported or modeled downtime.

* **4. Incident Categories to Monitor:**
  Select from *Operational Disruption*, *Environmental & Regulatory*, and *Logistics Disruption*.

* **Launch:**  
  Click the green **`[Start Investigation →]`** button at the bottom right.

### Step 3: Gathering Details Loading Screen
Immediately upon clicking **`[Start Investigation →]`**, the interface transitions to the **Gathering Details Loading Screen**:
* **Live Forensic Stepper:** Shows real-time progress across 5 distinct pipeline stages:
  1. *Intelligence Ingestion:* Queries public sources & news wires with SSRF safety checks.
  2. *Syndicated Wire Deduplication:* Clusters syndication copies (Reuters, AP, Bloomberg) into singular reporting groups.
  3. *Nebius Cloud Neural Reasoning:* Runs `nvidia/Nemotron-3_5-Lightning` with full reasoning tokens to structure claims without hallucinations.
  4. *Deterministic Verification:* Enforces Rule E-005 exact substring character matching and Rule ID-001 entity disambiguation.
  5. *Operational Exposure Calculation:* Balances reported downtime against your warehouse safety stock buffer (Formula EX-003).
* **Live Stopwatch:** Tracks elapsed inference seconds ($T+00:08\text{s}$).
* **Target Profile Badge:** Displays supplier name, part number, safety stock days, and inference model ID.

### Step 4: Forensic Workspace & Evidence Inspection
Once the pipeline finishes, the screen seamlessly transitions into the **Forensic Workspace**:
- **Operational Exposure Card:** Visualizes your safety stock vs estimated disruption days.
  - *Example:* If estimated recovery is 45 days and buffer is 14 days, Sentinel calculates a **31-Day Net Disruption Exposure**.
- **Incident Candidate Summary:** Shows the incident type (e.g., *Operational Disruption - Cleanroom Fire*), severity level, and facility location.
- **Evidence Claims & Exact Quotes:** 
  - Every claim has a green `exact_match` badge showing verified substring grounding.
  - Inspect exact start and end character offsets.
- **Reporting Lineage:** Shows how many independent reporting groups corroborate the incident versus syndication copies.
- **Contradiction Detection:** Highlights if a follow-up source reports that operations resumed or that the incident was merely a drill.

### Step 5: Human-in-the-Loop Decision Gate
Located at the bottom of the Forensic Workspace:
1. Sentinel generates a deterministic **Policy Recommendation** based on the rulebook:
   - `invoke_dual_sourcing` (for critical positive gaps).
   - `expedite_shipment` (for moderate gaps).
   - `monitor_only` (for zero gap or non-impacting incidents).
   - `dismiss_false_positive` (for entity or facility mismatches).
2. The human procurement officer selects an action:
   - **Approve Recommendation**
   - **Override Recommendation** (select an alternate policy from the dropdown)
   - **Dismiss as False Positive**
3. Enter your **Reviewer Name** and **Justification Notes**.
4. Click **"Commit Review Decision"**. The decision is permanently registered in the audit ledger and cannot be altered.

### Step 6: Suppliers Management & Inventory Buffer
Click **Suppliers** in the sidebar:
- View all registered vendors, locations, domains, and criticality ratings.
- Inspect linked components and their current inventory buffer days.
- Click **"Investigate"** next to any vendor to initiate a fresh live incident sweep.

### Step 7: Immutable Audit Trail
Click **Audit Trail** in the sidebar:
- Inspect every action taken by the system and users.
- Events logged include: `investigation_created`, `pipeline_step_completed`, `entity_resolved`, `recommendation_generated`, and `human_decision_recorded`.
- Provides full compliance transparency for enterprise supply chain audits.

---

## 5. The Three Benchmark Challenge Scenarios

In the **New Investigation** view, click on any of the 3 scenario pre-fills to test the edge-case safeguards:

| Scenario Card | Event Description | Key Challenge | Sentinel Behavior |
|:---|:---|:---|:---|
| **Cleanroom Fire (Dresden)** | Wafer fab cleanroom fire halting 300mm output for 45 days. Buffer is 14 days. | Direct Disruption & Net Exposure | Calculates +31-day net gap. Multi-signal confirms Dresden fab. Recommends **Invoke Dual Sourcing**. |
| **Substation Incident (Titan)** | Explosion at regional distribution substation near battery plant. | Non-Impacting Facility Event | Detects line equipment is unharmed. Net gap is 0 days. Recommends **Monitor Only**, preventing false panic. |
| **Cyber Alert (Vertex)** | News report of ransomware at "Vertex Ltd" based in Melbourne, Australia. | Corporate Homonym Disambiguation | Identifies geographic mismatch (Australia vs UK). Blocks escalation, protecting supplier relationship. |

---

## 6. System Diagnostics & Operator Verification

Click **"System Diagnostics"** at the bottom of the left sidebar to open the diagnostics inspector:
- **LLM Provider:** Shows `nebius` (Active).
- **Model ID:** `nvidia/Nemotron-3_5-Lightning`.
- **Nebius Connectivity:** Verifies active API authentication, reachable base URL, and model availability.
- **Database:** Confirms SQLite connection pool status and schema migrations.
- **Search Provider:** Shows active search adapter (DuckDuckGo Live / Tavily).

---

## 7. Programmatic REST API Guide

For automated ERP integrations or batch evaluation scripts:

### Check System Health
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### Check Nebius Provider Health
```bash
curl -X GET "http://localhost:8000/api/v1/health/providers"
```

### Trigger an Investigation via API
```bash
curl -X POST "http://localhost:8000/api/v1/investigations" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "Silicon Foundry Dresden GmbH",
    "part_name": "Automotive Microcontroller MCU-4",
    "coverage_days": 14,
    "recovery_days": 45,
    "search_mode": "ddg",
    "criticality": "high"
  }'
```

### Inspect OpenAPI Documentation
Open [http://localhost:8000/api/docs](http://localhost:8000/api/docs) in any browser for full interactive Swagger definitions with request/response schemas.

---

## 8. Troubleshooting & Common Questions

### 1. What happens if an article paraphrases a quote?
Sentinel flags the quote as `quote_mismatch`. It refuses to rely on paraphrased quotes for severe escalation decisions, requiring exact character grounding.

### 2. Can I run Sentinel without an internet connection?
Yes. Select **Deterministic Fixtures** mode in the New Investigation view or run `evaluation/runner.py` offline. The deterministic evaluation suite tests all 20 challenge scenarios with zero cloud dependencies.

### 3. How do I change the safety stock inventory buffer?
In the **Suppliers** tab, select the supplier, edit the linked part's `coverage_days`, or specify it directly when launching a New Investigation.

---

*SupplyChain Sentinel — Engineered for the Nebius × NVIDIA Global AI Hackathon.*
