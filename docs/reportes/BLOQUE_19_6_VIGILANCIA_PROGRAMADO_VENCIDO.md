# BLOQUE 19.6 — Vigilancia automática de PROGRAMADO vencido

## SLA
- normal <= 6h
- alerta >= 6h y < 24h
- vencido >= 24h

## Resumen por mercado
| Mercado | PROGRAMADO total | SANO | AMARILLO | VENCIDO |
|---|---:|---:|---:|---:|
| CORNERS_1T | 16 | 8 | 8 | 0 |
| CORNERS_LOCAL_1T | 16 | 8 | 8 | 0 |

## Señal operativa
- Tipo: calendario_real_sin_vencidos
- Abrir bloque ingestión/resultados: NO
- Mensaje: No hay PROGRAMADO vencidos; el bloqueo actual sigue siendo calendario real.