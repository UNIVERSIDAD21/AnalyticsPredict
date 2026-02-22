#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
AUTO_KILL_PORTS="${AUTO_KILL_PORTS:-true}"

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
  fuser -k "${BACKEND_PORT}/tcp" >/dev/null 2>&1 || true
  fuser -k "${FRONTEND_PORT}/tcp" >/dev/null 2>&1 || true
fi

# Backend
cd "$BACKEND_DIR"
if [[ -f ".venv/bin/activate" ]]; then
  echo "[dev] Usando backend/.venv"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  PYTHON_BIN="python"
else
  echo "[dev] .venv inválido/no disponible, usando python3 del sistema"
  PYTHON_BIN="python3"
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