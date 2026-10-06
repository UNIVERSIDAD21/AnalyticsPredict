#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
AUTO_KILL_PORTS="${AUTO_KILL_PORTS:-false}"

cleanup() {
  echo
  echo "[dev] Cerrando procesos..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[dev] Root: $ROOT_DIR"

if [[ "$AUTO_KILL_PORTS" == "true" ]]; then
  echo "[dev] Liberando puertos $BACKEND_PORT y $FRONTEND_PORT (si están ocupados)..."

  kill_port() {
    local port="$1"

    if command -v fuser >/dev/null 2>&1; then
      fuser -k "${port}/tcp" >/dev/null 2>&1 || true
      return
    fi

    if command -v lsof >/dev/null 2>&1; then
      local pids
      pids="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
      [[ -n "$pids" ]] && kill $pids >/dev/null 2>&1 || true
      return
    fi

    echo "[dev] Aviso: no se encontró fuser ni lsof; no se pudo liberar el puerto $port automáticamente."
  }

  kill_port "$BACKEND_PORT"
  kill_port "$FRONTEND_PORT"
fi

# Backend
cd "$BACKEND_DIR"
if [[ -n "${BACKEND_PYTHON:-}" ]]; then
  PYTHON_BIN="$BACKEND_PYTHON"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi
if ! "$PYTHON_BIN" -c 'import fastapi, uvicorn, psycopg' >/dev/null 2>&1; then
  echo "[dev] Python backend no disponible o sin dependencias: $PYTHON_BIN" >&2
  echo "[dev] Crea backend/.venv e instala backend/requirements.txt, o define BACKEND_PYTHON." >&2
  exit 1
fi

echo "[dev] Levantando backend en http://$BACKEND_HOST:$BACKEND_PORT"
$PYTHON_BIN -m uvicorn app:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID=$!

# Frontend
cd "$FRONTEND_DIR"
if [[ ! -d node_modules ]]; then
  echo "[dev] Instalando dependencias frontend..."
  npm install
fi

echo "[dev] Levantando frontend en http://$FRONTEND_HOST:$FRONTEND_PORT"
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo "[dev] Backend PID:  $BACKEND_PID"
echo "[dev] Frontend PID: $FRONTEND_PID"
echo "[dev] Swagger: http://localhost:$BACKEND_PORT/docs"
echo "[dev] Frontend: http://localhost:$FRONTEND_PORT"

echo "[dev] Presiona Ctrl+C para detener ambos servicios"
wait
