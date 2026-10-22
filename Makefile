# SupplyChain Sentinel — Developer convenience commands
# Usage: make <target>
# Requires: Python 3.12, Node.js 18+, Ollama

ifeq ($(OS),Windows_NT)
    VENV_BIN := backend/venv/Scripts
    PYTHON   := backend/.venv/Scripts/python.exe
    PYTEST   := backend/.venv/Scripts/pytest.exe
    RUFF     := backend/.venv/Scripts/ruff.exe
else
    VENV_BIN := backend/.venv/bin
    PYTHON   := $(VENV_BIN)/python
    PYTEST   := $(VENV_BIN)/pytest
    RUFF     := $(VENV_BIN)/ruff
endif

.PHONY: install install-backend install-frontend
.PHONY: dev dev-backend dev-frontend
.PHONY: test lint format doctor
.PHONY: build typecheck

# ---- Install ------------------------------------------------
install: install-backend install-frontend

install-backend:
	cd backend && py -3.12 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -e "backend[dev]"

install-frontend:
	cd frontend && npm install

# ---- Dev servers --------------------------------------------
dev-backend:
	$(PYTHON) -m uvicorn app.main:app --reload --port 8000 --app-dir backend

dev-frontend:
	cd frontend && npm run dev

# ---- Tests --------------------------------------------------
test:
	cd backend && $(PYTEST) tests/ -v --tb=short

test-unit:
	cd backend && $(PYTEST) tests/unit/ -v --tb=short

# ---- Lint / format ------------------------------------------
lint:
	$(RUFF) check backend/app/ backend/tests/

format:
	$(RUFF) format backend/app/ backend/tests/

format-check:
	$(RUFF) format --check backend/app/ backend/tests/

typecheck:
	cd frontend && npm run typecheck

# ---- Provider health ----------------------------------------
doctor:
	@echo "=== Python version ==="
	$(PYTHON) --version
	@echo "=== Ollama status ==="
	$(PYTHON) -c "import asyncio; from app.providers.ollama_provider import make_ollama_provider_from_settings; import sys; sys.path.insert(0,'backend'); asyncio.run(make_ollama_provider_from_settings().health_check())"
	@echo "Run 'ollama pull qwen3.5:9b' if model is not available"

# ---- Frontend build -----------------------------------------
build:
	cd frontend && npm run build

# ---- Unified Production Hosting -----------------------------
host: build
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend

docker-build:
	docker build -t supplychain-sentinel .

docker-run:
	docker run -p 8000:8000 -v sentinel-data:/app/data supplychain-sentinel
