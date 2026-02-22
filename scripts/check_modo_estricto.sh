#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SCORE_MINIMO="${SCORE_MINIMO:-75}"

curl -sSf "$BASE_URL/api/metricas/modo-estricto?score_minimo=$SCORE_MINIMO" | python3 -m json.tool