# syntax=docker/dockerfile:1

# ---- Stage 1: build the frontend static export ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend serving API + static frontend ----
FROM python:3.12-slim AS backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY backend/ ./

RUN uv sync --frozen --no-dev

# app/main.py locates the frontend build relative to its own path assuming
# backend/ and frontend/ are sibling directories, same as the source repo —
# so the static export is copied to /app/frontend/out, not alongside backend/.
COPY --from=frontend-build /frontend/out /app/frontend/out

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
