# PLAN_DE_SEPARACION_NBA_FOOTBALL

Versión: 1.0  
Fecha: 2026-03-09

## 1. Separaciones inmediatas SIN riesgo

| Item | Cambio | Riesgo | Estado |
|---|---|---|---|
| Prefix claro en routers por dominio | Mantener rutas explícitas NBA/FUT | Bajo | Ya aplicado |
| Etiquetado dominio en logging estructurado | Agregar `domain` en logs críticos | Bajo | Parcial |
| Separar documentación por dominio | Documentos específicos en `docs/borlty-context` | Bajo | Aplicado |

## 2. Separaciones planificadas (requieren refactor)

| Sprint | Acción | Riesgo |
|---|---|---|
| S+1 | Extraer servicios `calidad_nba.py` y `calidad_futbol.py` con fachada común | Medio |
| S+1 | Separar DTOs de explicación por sport antes de mapear al contrato común | Medio |
| S+2 | Aislar pipelines de ingestión fútbol de módulos compartidos de alertas | Alto |

## 3. Qué NO tocar todavía

- `backend/explicabilidad/contrato.py` (núcleo canónico compartido)
- `backend/feature_flags.py` (control global)
- `backend/calidad/estado-sistema` (visibilidad de deuda B05 unificada)

## 4. Criterio de verificación

Smoke test requerido:
- falla intencional en motor_futbol no debe romper endpoints NBA básicos.

## 5. EJECUTADO (bloque 09)

| Fecha | Acción ejecutada | Evidencia |
|---|---|---|
| 2026-03-09 | No se aplicaron separaciones físicas de riesgo | decisión explícita de no-regresión |
| 2026-03-09 | Se añadió smoke test de separación de dominios | `backend/tests/test_separacion_dominios.py` |

> Reglas legacy de fútbol (`status`, `probabilidad`, `odds`, etc.) siguen como deuda activa y no se marcan resueltas.
