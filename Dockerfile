# Multi-stage Production Dockerfile for SupplyChain Sentinel
# Builds the production React frontend and hosts both API & UI from FastAPI.

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.12-slim AS runner
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/pyproject.toml /app/backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "/app/backend"

# Copy backend code
COPY backend /app/backend

# Copy built frontend assets into location where FastAPI mounts it
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Ensure data directory exists for persistent SQLite database
RUN mkdir -p /app/data

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATABASE_URL=sqlite+aiosqlite:////app/data/sentinel.db

VOLUME ["/app/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
