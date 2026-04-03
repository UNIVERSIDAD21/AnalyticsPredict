# BLOQUE 13 — Shadow/Paper Mode operativo y validación prolongada (fútbol)

## Decisión
Fútbol permanece en beta global. Se implementa capa de operación prolongada en modo shadow/paper para validar consistencia longitudinal por mercado sin sobreprometer madurez.

## 1) Definición formal de shadow/paper mode

- **Objetivo:** ejecutar análisis reales y acumular evidencia longitudinal antes de promoción.
- **Regla operativa:** todo mercado no `PROMOCIONABLE` opera en `PAPER_SHADOW`.
- **No comercialización implícita:** UI y trazabilidad indican explícitamente estado no promocionado.

## 2) Qué se registra y qué faltaba

Ya existía registro en `predicciones_futbol` (mercado, línea, probabilidad, outcome). Faltaba:
- consolidar métricas operativas por ventana temporal para seguimiento continuo,
- exponer estado operativo vigente de mercado para frontend/control,
- explicitar en respuesta de análisis si corre en modo paper/shadow.

## 3) Implementación

### Backend
- `backend/api/rutas_analisis_futbol.py`
  - añade en `objetivo.trazabilidad`:
    - `modo_operativo: PAPER_SHADOW|PROMOCIONABLE_ACTIVO`

- `backend/api/rutas_metricas_futbol.py`
  - nuevo endpoint `GET /api/futbol/metricas/shadow-operativo`
  - devuelve por mercado (por ventana semanal/quincenal/mensual):
    - análisis emitidos,
    - resolubles pendientes,
    - resueltos,
    - tasa de resolución,
    - coverage de líneas,
    - fallback rate,
    - brier,
    - estado operativo vigente,
    - modo operativo.

### Pipeline de reporte longitudinal
- nuevo script `backend/scripts/reporte_shadow_mode_futbol.py`
  - genera reporte por ventanas: semanal/quincenal/mensual
  - salida: `docs/reportes/BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json`

### Frontend
- `frontend/src/componentes/organismos/ResultadoAnalisis.tsx`
  - estado operativo visible del mercado,
  - si no es promocionable, banner explícito: `PAPER/SHADOW`.

## 4) Indicadores de validación prolongada

Monitoreados por mercado:
- cantidad de análisis emitidos,
- cantidad resoluble y resuelta,
- tasa de resolución,
- coverage de líneas,
- coherencia estado operativo vs desempeño (brier/fallback),
- degradación y estabilidad en ventanas.

## 5) Condición de salida de shadow mode

Un mercado sale de `PAPER_SHADOW` solo si queda `PROMOCIONABLE` en scorecard/gate y mantiene estabilidad por ventanas consecutivas según política de bloques 10-12.

## 6) Evidencia de ejecución

- `python backend/scripts/reporte_shadow_mode_futbol.py` ✅
- archivo generado: `docs/reportes/BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json`

## 7) Pruebas

Backend:
- `backend/tests/test_futbol_shadow_operativo.py`
- `backend/tests/test_futbol_madurez_beta.py`

Frontend:
- regresiones de análisis fútbol existentes (lint/test/build) ejecutadas.

## 8) Riesgos residuales

- Persistencia full de estado longitudinal depende de aplicar tabla canónica de bloque 11 en ambiente productivo.
- Advertencia de chunk circular frontend persiste como deuda técnica (no bloquea este bloque).
