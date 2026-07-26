#!/usr/bin/env bash
# One-command launcher for Aegis (venv, deps, .env, free port, uvicorn).
# Usage:
#   ./start.sh
#   ./start.sh --port 8000 --no-reload
#   ./start.sh --reinstall

set -euo pipefail
cd "$(dirname "$0")"

PORT=8000
HOST="127.0.0.1"
RELOAD=1
SKIP_PORT_KILL=0
REINSTALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="${2:-8000}"; shift 2 ;;
    --host) HOST="${2:-127.0.0.1}"; shift 2 ;;
    --no-reload) RELOAD=0; shift ;;
    --skip-port-kill) SKIP_PORT_KILL=1; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help)
      echo "Usage: ./start.sh [--port N] [--host ADDR] [--no-reload] [--skip-port-kill] [--reinstall]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

banner() {
  echo ""
  echo "  ========================================"
  echo "               A E G I S"
  echo "      SRE copilot for SigNoz"
  echo "  ========================================"
  echo ""
}

resolve_python() {
  local candidates=("python3.13" "python3.12" "python3.11" "python3" "python")
  local cmd ver major minor
  for cmd in "${candidates[@]}"; do
    command -v "$cmd" >/dev/null 2>&1 || continue
    ver="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    [[ -z "$ver" ]] && continue
    major="${ver%%.*}"
    minor="${ver#*.}"
    if [[ "$major" -gt 3 ]] || { [[ "$major" -eq 3 ]] && [[ "$minor" -ge 10 ]]; }; then
      echo "$cmd"
      return 0
    fi
  done
  echo "Python 3.10+ not found. Install Python 3.11+ and retry." >&2
  exit 1
}

free_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids:-}" ]]; then
      echo "Freeing port $port (PIDs: $pids)..."
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" 2>/dev/null || true
  fi
}

banner

PY="$(resolve_python)"
VER="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Python: $VER via $PY"

if [[ "$REINSTALL" -eq 1 && -d .venv ]]; then
  echo "Removing existing .venv (reinstall)..."
  rm -rf .venv
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating virtualenv..."
  "$PY" -m venv .venv
fi

if [[ ! -x .venv/bin/uvicorn || "$REINSTALL" -eq 1 ]]; then
  echo "Installing dependencies from requirements.txt..."
  .venv/bin/python -m pip install -U pip --quiet
  .venv/bin/python -m pip install -r requirements.txt
fi

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "uvicorn not found after install. Check requirements.txt" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "Created .env from .env.example"
    echo "  → set SIGNOZ_URL, SIGNOZ_API_KEY, and OTEL_EXPORTER_OTLP_HEADERS"
  else
    echo "Warning: .env.example missing — create .env manually."
  fi
fi

if [[ "$SKIP_PORT_KILL" -eq 0 ]]; then
  free_port "$PORT"
fi

RELOAD_ARGS=()
if [[ "$RELOAD" -eq 1 ]]; then
  RELOAD_ARGS=(--reload)
fi

echo ""
echo "Starting Aegis..."
echo "  UI      http://${HOST}:${PORT}/"
echo "  Docs    http://${HOST}:${PORT}/docs"
echo "  Health  http://${HOST}:${PORT}/api/v1/health"
echo "  Deep    http://${HOST}:${PORT}/api/v1/health/deep"
echo "  MCP     http://${HOST}:${PORT}/mcp"
echo "  Stop    Ctrl+C"
echo ""

exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT" "${RELOAD_ARGS[@]}"
