# Bitácora de apuestas analizadas

## Objetivo
Registrar automáticamente análisis generados (NBA/Fútbol) y actualizar su estado cuando el partido termina.

## Componentes
- Servicio backend: `backend/servicios/apuestas_analizadas.py`
- Endpoint listado: `GET /api/bitacora/apuestas-analizadas`
- Resolución automática: integrada en `api/rutas_internas.py` (ciclo de calidad)

## Campos clave
- `estado`: `PENDIENTE` / `FINALIZADA`
- `resultado_outcome`: `GANADA` / `PERDIDA` / `PUSH`
- `valor_real`: valor final resuelto según mercado
- `payload`: contexto de predicción (probabilidades, marcador probable, etc.)

## Flujo
1. Al analizar un partido, se registra en `apuestas_analizadas`.
2. En ciclo de calidad se resuelven pendientes con resultado real.
3. UI consume métricas y listados para seguimiento operativo.

## Comandos útiles
```bash
# Backend smoke
python3 -m pytest -q backend/tests/test_smoke_api.py

# Frontend build
npm run build --prefix frontend

# Ejecutar ciclo local
python3 backend/scripts/ejecutar_ciclo_calidad_local.py --limite-baloncesto 2000 --limite-futbol 3000
```
