# Matriz de Decisiones de Modelo (Operación)

## Semáforo global

| Semáforo | Condición | Acción |
|---|---|---|
| Verde | score >= 85 | Operación normal + monitoreo semanal |
| Amarillo | 70 <= score < 85 | Recalibración selectiva + revisión diaria |
| Rojo | score < 70 | Incidente de calidad (playbook SEV-1) |

## Decisión por mercado

| Condición | Decisión |
|---|---|
| n_resueltas < 100 | No recalibrar automático, solo monitorear |
| Brier > 0.26 y n>=100 | Recalibración prioritaria |
| Deriva > 15% | Recalibración de emergencia |
| Brier <= 0.22 con estabilidad | Mantener calibrador actual |

## Política de publicación de calibradores
- Publicar solo si mejora mínima de Brier >= 0.005.
- Rechazar calibrador si empeora log-loss > 2%.
- Registrar versión, fecha y métricas antes/después.

## Política de recomendaciones
- Bloquear recomendaciones en mercados en rojo.
- Reducir stake/confianza en mercados amarillos.
- Operación completa solo en mercados verdes.

## Frecuencia recomendada
- Ciclo calidad: diario.
- Revisión ejecutiva: diario.
- Recalibración programada: semanal.
- Recalibración de emergencia: según deriva.
