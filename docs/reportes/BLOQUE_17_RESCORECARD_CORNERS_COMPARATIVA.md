# BLOQUE 17 — Re-scorecard comparativa corners rescatados

## Decisión
- aún no suben de estado; vale la pena seguir acumulando masa resolutiva en estos dos mercados

## Tabla antes vs después
| Mercado | Resueltos binarios (antes->después) | Cerrados operativos (antes->después) | Pendientes (antes->después) | Líneas | Fallback | Estado final |
|---|---:|---:|---:|---:|---:|---|
| CORNERS_1T | 4 -> 4 | 12 -> 12 | 24 -> 16 | 4 -> 4 | 0.0 -> 0.0 | BLOQUEADO |
| CORNERS_LOCAL_1T | 4 -> 4 | 12 -> 12 | 24 -> 16 | 4 -> 4 | 0.0 -> 0.0 | BLOQUEADO |

## Lectura de robustez
- No se sobreinterpreta Brier/LogLoss/ECE con n binario pequeño.
- Con 4 outcomes binarios, las métricas de calibración siguen siendo no representativas para promoción.

## Riesgos residuales
- Base resolutiva binaria mínima.
- Muchos partidos aún en PROGRAMADO (pendientes reales, no espurios).

## Siguiente frente
- Mantener foco en estos 2 mercados y acumular outcomes reales; luego re-scorecard en ventana siguiente.