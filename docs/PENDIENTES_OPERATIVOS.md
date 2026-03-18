# Pendientes Operativos

## Pendiente inmediato (bloqueado por approval/runtime)
1. ✅ Runtime de `GET /api/metricas/recomendaciones-accion` validado vía tests API + contrato (incluye nuevo control `max_acciones` y normalización de acciones).
2. Ejecutar compilación final de `rutas_metricas.py` tras último bloque.
3. Correr `make qa-preflight` y `make calidad-ciclo` completo con evidencia en `reports/`.

## Pendientes de mejora (siguiente fase)
1. Recalibración automática por mercado con umbrales (Brier/ECE/deriva).
2. Resolver predicciones de fútbol con ventana histórica de partidos FINALIZADO y completar outcomes.
3. Alerta de datos stale (ingestión) por deporte y competición.

## Avances ya implementados
- Endpoint drift por mercado con severidad.
- Reporte semanal automático completo.
- Semáforo/score de salud visible en frontend principal.
- Tests de integración para endpoints profesionales de métricas.
- Policy gate de mercados (fútbol y NBA) para bloquear recomendaciones en mercados degradados.
- Export CSV para BI (calidad/drift/política).
- Snapshot histórico de tendencias (`snapshot_tendencias.sh`).
