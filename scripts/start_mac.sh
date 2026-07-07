#!/usr/bin/env bash
# Idempotent start script for FinAlly (macOS/Linux).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="finally"
CONTAINER_NAME="finally"

cd "$PROJECT_ROOT"

if [ ! -f .env ]; then
  echo "No .env file found — copying .env.example to .env."
  echo "Edit .env and add your OPENROUTER_API_KEY before using AI chat."
  cp .env.example .env
fi

PORT="$(grep -E '^HOST_PORT=' .env 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
PORT="${PORT:-8000}"

mkdir -p db

BUILD=false
if [[ "${1:-}" == "--build" ]]; then
  BUILD=true
fi

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  BUILD=true
fi

if [ "$BUILD" = true ]; then
  echo "Building $IMAGE_NAME image..."
  docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"
fi

if [ "$(docker ps -a -q -f name="^${CONTAINER_NAME}$")" ]; then
  if [ "$(docker ps -q -f name="^${CONTAINER_NAME}$")" ]; then
    echo "FinAlly is already running at http://localhost:${PORT}"
    exit 0
  fi
  echo "Removing stopped container ${CONTAINER_NAME}..."
  docker rm "$CONTAINER_NAME" >/dev/null
fi

CONFLICTING_CONTAINER="$(docker ps --filter "publish=${PORT}" --format '{{.Names}}' 2>/dev/null | grep -v "^${CONTAINER_NAME}$" || true)"
if [ -n "$CONFLICTING_CONTAINER" ]; then
  echo "Error: port ${PORT} is already in use by Docker container '${CONFLICTING_CONTAINER}'." >&2
  echo "Stop that container, or set HOST_PORT in .env to a free port and rerun this script." >&2
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  PORT_OWNER="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}' || true)"
  if [ -n "$PORT_OWNER" ]; then
    echo "Error: port ${PORT} is already in use by ${PORT_OWNER}." >&2
    echo "Stop that process, or set HOST_PORT in .env to a free port and rerun this script." >&2
    exit 1
  fi
fi

echo "Starting FinAlly..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -v "$PROJECT_ROOT/db:/app/db" \
  -p "${PORT}:8000" \
  --env-file "$PROJECT_ROOT/.env" \
  "$IMAGE_NAME"

echo "FinAlly is running at http://localhost:${PORT}"
