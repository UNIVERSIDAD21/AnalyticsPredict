# MIGRACION_CONTRATO_LEGACY

Fecha: 2026-03-09  
Versión: 1.0

## 1. Inventario de consumidores conocidos (legacy)

1. Clientes que llaman `GET /api/prediccion/{id}/explicacion?version=legacy`.
2. Clientes que envían header `Accept: application/json; version=legacy`.
3. Integraciones heredadas del bloque 05 que esperan envelope legacy (`id`, `deporte`, `confianza`, `calidad_nivel`, etc.).

## 2. Telemetría implementada

- Tabla: `analytics.contrato_uso_log`.
- Métricas por `fecha + domain`:
  - `total_llamadas_v1`
  - `total_llamadas_legacy`
- Log estructurado por request con `is_legacy_contract`.

## 3. Deprecation headers

Toda respuesta legacy incluye:
- `Deprecation: true`
- `Sunset: <fecha>`
- `Link: </api/prediccion/{id}/explicacion?version=v1>; rel="successor-version"`

## 4. Criterio técnico de sunset

Se define sunset cuando se cumpla cualquiera:
1. Uso legacy < 5% del total por 7 días consecutivos.
2. Fecha máxima de migración: **2026-12-31** (tope bloque 10).

La lógica actual calcula sunset dinámico:
- Si cumple criterio (1): `hoy + 30 días` (limitado por fecha tope).
- Si no cumple: fecha tope `2026-12-31`.

## 5. Plan de comunicación

1. Publicar changelog semanal con ratio legacy/v1 por dominio.
2. Notificar consumidores legacy cuando deprecation headers aparezcan en producción.
3. Enviar recordatorio de sunset 90/60/30 días.
4. Bloque 10: retirar legacy solo si criterio técnico está cumplido y aprobaciones completas.

## 6. Estado de deuda (explícito)

- `contratos_legacy_coexistentes_bloque_05` -> `EN_MIGRACION`.
- No se elimina contrato legacy en este bloque.
- Seguimiento continúa hasta bloque 10+.
