# Contributing to SupplyChain Sentinel (https://github.com/Aditya-230707/SupplyChain-Sentinel)

Thank you for your interest in contributing to SupplyChain Sentinel! This project is an evidence-first, deterministic supplier incident intelligence platform designed to eliminate LLM hallucinations, duplicate news-wire false alarms, and premature operational disruptions.

---

## Core Philosophy

When contributing to this repository, keep these foundational rules in mind:

1. **Evidence First, Generative Second**: Never rely on raw LLM output for critical decisions. Model extractions are untrusted until mathematically verified (e.g., exact substring quote matching in rule `E-005`).
2. **Deterministic Policies**: Decision recommendations (`urgent_human_review`, `monitor`, etc.) are computed exclusively by Python policy functions (`P-001` through `P-010`), never generated free-form by LLMs.
3. **Null-Safety Over Guesswork**: If recovery duration or inventory levels are unknown, values remain explicitly `None`. Never default missing numbers to zero or fabricate risk metrics.
4. **Human in the Loop**: Autonomous actions (freezing purchase orders, cancelling contracts) are prohibited. Sentinel assists human reviewers; it does not replace them.
5. **Simple > Clever**: Write readable, well-commented, maintainable code. Avoid over-engineering, unnecessary abstractions, or massive framework refactors.

---

## Development Setup

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** and **npm**
- **Git**

### 1. Repository Setup
```bash
git clone https://github.com/Aditya-230707/SupplyChain-Sentinel.git
cd SupplyChain-Sentinel
cp .env.example .env
```
*(On Windows PowerShell, use `copy .env.example .env`).*

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

Start the backend development server:
```bash
uvicorn app.main:app --reload --port 8000
```
- API is available at: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
- Frontend application is available at: `http://localhost:5173`

---

## Quality Gates & Verification

Before submitting a pull request, all automated checks must pass cleanly.

### Backend Checks
```bash
# Run backend test suite (95+ unit and integration tests)
pytest backend/tests/unit/ -m "not slow"

# Run Ruff linter
ruff check backend evaluation

# Run Ruff formatter check
ruff format --check backend evaluation
```

### Frontend Checks
```bash
cd frontend

# TypeScript type check (strict, zero errors)
npm run typecheck

# ESLint check (zero warnings, zero errors)
npm run lint

# Production build test
npm run build
```

---

## Testing Guidelines

- **Keep Tests Offline**: Unit tests must never make external network calls. Use `FixtureSearchProvider` or mock HTTP endpoints using `respx` or `unittest.mock`.
- **Live Smoke Tests**: Live provider tests (e.g. Nebius Token Factory) must be gated behind explicit environment flags (such as `ALLOW_LIVE_SMOKE_TESTS=true`).
- **Benchmark Integrity**: If you modify entity resolution, quote verification, or policy evaluation logic, run `python evaluation/runner.py` to ensure benchmark metrics do not regress.

---

## Submitting Pull Requests

1. **Branch Naming**: Use descriptive branch names like `fix/lineage-url-parser` or `feature/custom-policy-rules`.
2. **Keep PRs Focused**: Avoid combining large structural changes with unrelated bug fixes.
3. **Commit Messages**: Write clear, descriptive commit messages.
4. **Documentation**: Update docstrings, `README.md`, or architecture diagrams if modifying API endpoints or schemas.
5. **No Secrets**: Never commit `.env` files, API keys, or production database files.

Thank you for helping make automated supply chain intelligence reliable and verifiable!
