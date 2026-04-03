# BLOQUE 12 — Monitoreo continuo y auto-demotion por mercado (fútbol)

## Objetivo
Evitar estados congelados: un mercado puede subir por evidencia, pero también debe bajar automáticamente cuando se deteriora.

## Implementación

### 1) Lógica de auto-demotion (core)
Archivo:
- `backend/motor_futbol/madurez_beta.py`

Nueva regla:
- `aplicar_autodemotion(estado_actual, estado_objetivo, motivos)`
- Permite **bajar automáticamente** (`PROMOCIONABLE -> VALIDACION -> LABORATORIO -> BLOQUEADO`).
- No permite subir automáticamente (promoción sigue siendo proceso explícito).

### 2) Pipeline de monitoreo continuo
Script nuevo:
- `backend/scripts/monitoreo_autodemotion_futbol.py`

Evalúa por mercado (ventana temporal configurable):
- coverage y líneas,
- volumen total/resuelto,
- Brier,
- Log Loss,
- fallback rate,
- estado objetivo vs estado actual,
- decisión de auto-demotion + motivos.

Salida:
- JSON reproducible con decisiones por mercado.
- Opción `--apply` para persistir degradaciones en tabla canónica.

### 3) Exposición backend para frontend/control
Endpoint nuevo:
- `GET /api/futbol/metricas/estado-operativo-mercados`

Retorna estado vigente por mercado desde tabla `futbol_estado_operativo_mercado` (si existe).

## Evidencia de ejecución

Comando ejecutado:
- `python backend/scripts/monitoreo_autodemotion_futbol.py --days 60 --out docs/reportes/BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json`

Artefacto generado:
- `docs/reportes/BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json`

## Pruebas

- `backend/tests/test_futbol_madurez_beta.py`
  - cobertura de mapeo de estados
  - auto-demotion cuando corresponde
  - no auto-promoción
- `backend/tests/test_futbol_walkforward_scorecard.py`

Resultado:
- 7 tests passing.

## Dependencias y gobernanza

Depende de:
- scorecards de bloque 10,
- política formal de bloque 11,
- tabla canónica `futbol_estado_operativo_mercado` (si se quiere persistencia automática con `--apply`).

## Riesgos residuales

- Si no se aplica la migración de tabla en ambiente objetivo, el monitoreo corre en modo reporte (sin persistencia).
- La promoción sigue siendo manual/controlada por diseño (evita auto-promoción por ruido estadístico).
