#!/usr/bin/env bash
# Idempotent stop script for FinAlly (macOS/Linux).
# Stops and removes the container; the db/ volume mount is left untouched.
set -euo pipefail

CONTAINER_NAME="finally"

if [ "$(docker ps -a -q -f name="^${CONTAINER_NAME}$")" ]; then
  echo "Stopping FinAlly..."
  docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
  echo "FinAlly stopped."
else
  echo "FinAlly is not running."
fi
