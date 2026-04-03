# BLOQUE 11 — Política formal de salida beta y promoción parcial por mercados (fútbol)

## Decisión principal
Se mantiene el estado global de fútbol en **BETA/LABORATORIO**.
No se elimina beta global. Se formaliza una política auditable por mercado con transición reversible.

## 1) Fuente de verdad actual
- Estado global y criterios cuantitativos vigentes provienen de:
  - `backend/config/futbol_politica_promocion.json` (política canónica)
  - `docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.json` (evidencia temporal)
  - endpoint `GET /api/futbol/metricas/madurez-beta` (estado operativo calculado)

## 2) Estados operativos por mercado
Definidos formalmente:
- `BLOQUEADO`
- `LABORATORIO`
- `VALIDACION`
- `PROMOCIONABLE`

Para cada estado se definió:
- significado técnico,
- significado visible en producto,
- requisitos de entrada/permanencia,
- causas de degradación/salida.

## 3) Criterios de transición (cuantitativos)
Base en scorecard walk-forward:
- volumen resuelto mínimo,
- coverage mínimo de líneas,
- Brier / LogLoss / ECE dentro de umbral,
- fallback/degradación controlada,
- estabilidad por ventanas (drift).

Umbrales canónicos guardados en `backend/config/futbol_politica_promocion.json`.

## 4) Integración backend
- Nuevo endpoint:
  - `GET /api/futbol/metricas/politica-promocion` (lee política canónica)
- `rutas_analisis_futbol` ahora inyecta en `objetivo.trazabilidad`:
  - `estado_operativo_mercado`
  - `motivos_estado_operativo`

Además se deja propuesta de persistencia auditable:
- `backend/scripts/sql/bloque_11/01_tabla_estado_operativo_mercado.sql`

## 5) Integración frontend
En `ResultadoAnalisis`:
- se muestra estado operativo del mercado de forma explícita,
- si gate crítico está activo, se mantiene modo beta/validación y se evita tratar el mercado como soporte serio.

## 6) Evidencia y pruebas
- Walk-forward + scorecard ya ejecutado en bloque 10.
- Pruebas backend:
  - `backend/tests/test_futbol_madurez_beta.py`
  - `backend/tests/test_futbol_walkforward_scorecard.py`
- Pruebas frontend:
  - `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
  - `frontend/src/servicios/futbol/analisis.test.ts`

## 7) Resultado operativo actual
Con la evidencia actual, el módulo continúa en beta global y la promoción debe ser **parcial por mercado** únicamente cuando un mercado cumpla umbrales sostenidos.

## 8) Riesgos residuales
- Persisten mercados con evidencia insuficiente para salir de laboratorio.
- La tabla de estado operativo quedó definida como artefacto de gobernanza; aplicar migración en entorno operativo según ventana de despliegue.
