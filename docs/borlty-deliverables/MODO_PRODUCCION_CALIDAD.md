# Modo Producción de Calidad (Checklist Único)

## Objetivo
Operar AnalyticsPredict con disciplina diaria, minimizando degradación de calidad.

## Inicio de jornada (5 min)
1. Verificar API:
   ```bash
   curl -sSf http://127.0.0.1:8000/salud
   ```
2. Ejecutar preflight:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make qa-preflight
   ```
3. Ejecutar ciclo de calidad:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo-fast
   ```
4. Revisar tablero:
   - `GET /api/metricas/tablero-salud`
   - `GET /api/metricas/recomendaciones-accion`
   - `GET /api/metricas/modo-estricto`

## Cierre de jornada (5 min)
1. Ejecutar ciclo completo:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo
   ```
2. Generar reporte ejecutivo:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make reporte-ejecutivo
   ```
3. Guardar enlace/ruta del reporte del día en bitácora interna.

## Reglas operativas
- Si score_global < 70: activar playbook de incidente (SEV-1).
- Si mercado tiene Brier > 0.26 y n>=100: recalibración prioritaria.
- Si deporte con n_resueltas=0 y n_total>0: bloquear decisiones automáticas basadas en ese deporte.

## Entregables diarios
- Snapshot salud
- Snapshot calidad mercados
- Recomendaciones de acción
- Reporte ejecutivo markdown
