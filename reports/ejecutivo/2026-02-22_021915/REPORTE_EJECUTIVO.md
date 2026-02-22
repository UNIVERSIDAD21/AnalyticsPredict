# Reporte ejecutivo de calidad

- score_global: 83
- semaforo_global: amarillo
- go_no_go: NO-GO
  - bloqueo: fuentes stale críticas 2 > permitido 0
  - bloqueo: futbol: n_total=243 sin predicciones resueltas

## Resumen compacto (30s)
- GO/NO-GO: NO-GO
- score: 83 | semaforo: amarillo
- alertas_criticas: 0
- top: [P1/rojo] Ejecutar ciclo de resolución para futbol
- top: [P1/rojo] Recalibrar mercado baloncesto/Q3
- top: [P1/rojo] Recalibrar mercado baloncesto/Q4

## Estado por deporte
- baloncesto: n_total=2178 n_resueltas=2152 brier=0.21788752106877324 accuracy=0.6700743494423792
- futbol: n_total=243 n_resueltas=0 brier=None accuracy=None

## Alertas de ingestión
- resumen: 2 fuentes en estado crítico de actualización.
- ingestion_state_baloncesto: stale=True sev=critica horas=109.37
- ingestion_state_futbol: stale=True sev=media horas=None
- predicciones_registradas: stale=True sev=critica horas=216.2
- predicciones_futbol: stale=False sev=baja horas=5.89

## Sugerencias de umbrales
- baloncesto: warning=0.3 bloqueo=0.332 muestra=2152

## Acciones priorizadas
- [P1/rojo] Ejecutar ciclo de resolución para futbol — No hay predicciones resueltas; no se puede medir calidad real.
- [P1/rojo] Recalibrar mercado baloncesto/Q3 — Brier 0.306 con n=182.
- [P1/rojo] Recalibrar mercado baloncesto/Q4 — Brier 0.317 con n=150.