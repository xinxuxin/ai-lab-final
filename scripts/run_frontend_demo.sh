#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/backend"
source ../.venv/bin/activate
uvicorn app.main:app --reload --app-dir src --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd "$ROOT_DIR/frontend"
npm run dev -- --host 0.0.0.0
