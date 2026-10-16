# SupplyChain Sentinel

> Evidence-first supplier incident intelligence — Nebius × NVIDIA Global AI Hackathon 2026

---

## What it does

SupplyChain Sentinel investigates public reports about supplier disruptions and compliance incidents.
It checks whether evidence concerns the correct supplier and event, evaluates business exposure against
explicit buyer-provided data, and produces an auditable recommendation for human review.

**It does not autonomously suspend suppliers, modify purchase orders, or make procurement decisions.**

---

## Quick start (local development)

### Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.12 |
| Node.js | 18+ |
| Ollama | 0.4+ (running at `localhost:11434`) |
| Git | any recent version |

### 1 — Clone and configure

```powershell
git clone <repo-url>
cd Sentinel
copy .env.example .env
# Edit .env and set OLLAMA_MODEL, and optionally TAVILY_API_KEY / NEBIUS_API_KEY
```

### 2 — Pull a local model

```powershell
ollama pull qwen3.5:9b
```

### 3 — Backend setup

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 4 — Run backend

```powershell
# From backend/ with venv active:
uvicorn app.main:app --reload --port 8000
```

Health check: http://localhost:8000/api/v1/health

### 5 — Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Run tests

```powershell
# From backend/ with venv active:
pytest tests/ -v

# Lint and format:
ruff check app/ tests/
ruff format --check app/ tests/
```

Tests run **without** Ollama, Nebius, or Tavily access. External providers are mocked.

---

## Provider configuration

Set `LLM_PROVIDER` in `.env`:

| Value | When to use |
|---|---|
| `fake` | Unit tests (no network, deterministic) |
| `ollama` | Local development (requires Ollama + a pulled model) |
| `nebius` | Hackathon submission (requires `NEBIUS_API_KEY` + `NEBIUS_MODEL`) |

For the hackathon submission the core workflow runs through **Nebius Token Factory** using a verified **NVIDIA open-source model**.
Verify the exact model ID from your Token Factory console before setting `NEBIUS_MODEL`.

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full pipeline and module descriptions.

Key principles from the blueprint:
- Evidence before explanation — every factual brief statement links to a stored record.
- Deterministic code (not LLM) calculates inventory gaps and enforces policy rules.
- No autonomous high-impact actions — Sentinel recommends for human review only.
- Fail closed on missing evidence — unknown stays unknown, not zero.

---

## License

MIT — see [LICENSE](LICENSE).
