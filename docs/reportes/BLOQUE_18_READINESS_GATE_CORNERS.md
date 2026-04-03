# BLOQUE 18 — Umbral duro de masa resolutiva y gate de reevaluación

## Política aplicada
- Archivo: `backend/config/futbol_readiness_gate_corners_b18.json`
- Regla: Sin masa resolutiva mínima no se permite reevaluación seria ni promoción.

## Readiness por mercado foco
| Mercado | Masa actual | Req. reevaluación | Req. salir BLOQUEADO | Req. candidatura VALIDACIÓN | Coverage actual | Pendientes rate | Readiness | Gate reevaluación |
|---|---:|---:|---:|---:|---:|---:|---|---|
| CORNERS_1T | 4 | 30 | 60 | 120 | 4 | 0.5714 | NO_LISTO | BLOQUEADO |
| CORNERS_LOCAL_1T | 4 | 30 | 60 | 120 | 4 | 0.5714 | NO_LISTO | BLOQUEADO |

## Conclusión
- Mientras el gate de readiness esté BLOQUEADO, cualquier re-scorecard debe tratarse como no concluyente para promoción.
- Primero se acumula masa resolutiva y estabilidad temporal; luego se reabre reevaluación seria.