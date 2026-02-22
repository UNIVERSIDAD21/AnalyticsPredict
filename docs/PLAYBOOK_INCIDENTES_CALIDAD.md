# Playbook de Incidentes de Calidad de Predicción

## Objetivo
Responder rápido cuando el sistema degrada su calidad (score, Brier, deriva o backlog).

## Severidades

- **SEV-1 (Crítico)**
  - score_global < 70
  - deriva > 20% en cualquier deporte/mercado crítico
  - 0 resueltas por >48h con predicciones nuevas

- **SEV-2 (Alto)**
  - 70 <= score_global < 80
  - Brier > 0.26 en mercados core
  - backlog de pendientes creciendo 2 días seguidos

- **SEV-3 (Moderado)**
  - 80 <= score_global < 85
  - Brier en zona amarilla (0.22 - 0.26)

## Runbook rápido (SEV-1)
1. Ejecutar ciclo calidad inmediato:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo
   ```
2. Generar reporte ejecutivo:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make reporte-ejecutivo
   ```
3. Revisar:
   - `tablero_salud.json`
   - `calidad_mercados.json`
   - `recomendaciones_accion.json`
4. Congelar recomendaciones automáticas en mercados con Brier > 0.28.
5. Recalibrar mercados críticos (prioridad por volumen).
6. Revalidar a las 6h y 24h.

## Runbook SEV-2
1. Ejecutar `make calidad-ciclo-fast`.
2. Identificar top 5 mercados con peor Brier.
3. Programar recalibración en ventana del día.
4. Confirmar mejora (Brier_calibrado vs raw).

## Controles de salida del incidente
- score_global >= 85 por 2 corridas consecutivas.
- sin alertas críticas de deriva.
- backlog estable o decreciente.

## Postmortem mínimo
- Qué falló
- Qué mercado/deporte impactó
- Acción aplicada
- Métrica antes/después
- Prevención para evitar recurrencia
