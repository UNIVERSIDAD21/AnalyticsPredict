#!/bin/bash

# ══════════════════════════════════════════════════════════════
# Script de pruebas para la API del Analizador NBA
# ══════════════════════════════════════════════════════════════

BASE_URL="http://localhost:8000"

echo "═══════════════════════════════════════════════════════════"
echo " PRUEBAS DE API - ANALIZADOR NBA"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Prueba 1: Endpoint raíz
echo "📌 Prueba 1: Endpoint raíz (/)"
echo "────────────────────────────────────────"
curl -s "$BASE_URL/" | python -m json.tool
echo ""
echo ""

# Prueba 2: Health check
echo "📌 Prueba 2: Health check (/salud)"
echo "────────────────────────────────────────"
curl -s "$BASE_URL/salud" | python -m json.tool
echo ""
echo ""

# Prueba 3: Listar equipos
echo "📌 Prueba 3: Listar equipos (/api/equipos)"
echo "────────────────────────────────────────"
curl -s "$BASE_URL/api/equipos" | python -m json.tool
echo ""
echo ""

# Prueba 4: Análisis básico (sin cuota)
echo "📌 Prueba 4: Análisis básico Q1 (sin cuota)"
echo "────────────────────────────────────────"
curl -s -X POST "$BASE_URL/api/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "equipo_local": "LAL",
    "equipo_visitante": "GSW",
    "mercado": "Q1",
    "linea": 55.5
  }' | python -m json.tool
echo ""
echo ""

# Prueba 5: Análisis con cuota
echo "📌 Prueba 5: Análisis Q1 con cuota"
echo "────────────────────────────────────────"
curl -s -X POST "$BASE_URL/api/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "equipo_local": "LAL",
    "equipo_visitante": "GSW",
    "mercado": "Q1",
    "linea": 55.5,
    "cuota": 1.85
  }' | python -m json.tool
echo ""
echo ""

# Prueba 6: Análisis Q2
echo "📌 Prueba 6: Análisis Q2"
echo "────────────────────────────────────────"
curl -s -X POST "$BASE_URL/api/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "equipo_local": "BOS",
    "equipo_visitante": "MIA",
    "mercado": "Q2",
    "linea": 54.5
  }' | python -m json.tool
echo ""
echo ""

# Prueba 7: Análisis juego completo
echo "📌 Prueba 7: Análisis juego completo"
echo "────────────────────────────────────────"
curl -s -X POST "$BASE_URL/api/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "equipo_local": "DEN",
    "equipo_visitante": "PHX",
    "mercado": "COMPLETO",
    "linea": 225.5
  }' | python -m json.tool
echo ""
echo ""

# Prueba 8: Error - equipo inválido
echo "📌 Prueba 8: Error - equipo inválido"
echo "────────────────────────────────────────"
curl -s -X POST "$BASE_URL/api/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "equipo_local": "EQUIPO_FALSO",
    "equipo_visitante": "GSW",
    "mercado": "Q1",
    "linea": 55.5
  }' | python -m json.tool
echo ""
echo ""

# Prueba 9: Error - línea inválida
echo "📌 Prueba 9: Error - línea negativa"
echo "────────────────────────────────────────"
curl -s -X POST "$BASE_URL/api/analizar" \
  -H "Content-Type: application/json" \
  -d '{
    "equipo_local": "LAL",
    "equipo_visitante": "GSW",
    "mercado": "Q1",
    "linea": -10
  }' | python -m json.tool
echo ""
echo ""

# Prueba 10: Todos los cuartos
echo "📌 Prueba 10: Todos los cuartos (Q1-Q4)"
echo "────────────────────────────────────────"
for mercado in Q1 Q2 Q3 Q4; do
  echo "  → $mercado:"
  curl -s -X POST "$BASE_URL/api/analizar" \
    -H "Content-Type: application/json" \
    -d "{\n      \"equipo_local\": \"LAL\",\n      \"equipo_visitante\": \"GSW\",\n      \"mercado\": \"$mercado\",\n      \"linea\": 55.5\n    }" | python -c "import sys,json; d=json.load(sys.stdin); print(f'     Over: {d[\"datos\"][\"probabilidad_over\"]*100:.1f}%')" 2>/dev/null || echo "     Error"
done
echo ""
echo ""

echo "═══════════════════════════════════════════════════════════"
echo " FIN DE PRUEBAS"
echo "═══════════════════════════════════════════════════════════"
