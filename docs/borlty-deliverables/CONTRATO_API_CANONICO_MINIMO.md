# CONTRATO_API_CANONICO_MINIMO.md

## Objetivo
Definir convención mínima única para estabilización crítica (bloque 05, prioridad 3), sin migración masiva.

## Estado real detectado
Actualmente coexisten:
1. Éxito con envelope (`{ exito: true, ... }`)
2. Éxito con objeto directo (sin `exito`)
3. Errores FastAPI (`{ detail: "..." }`)
4. Errores con `message`/`mensaje`
5. Envelopes custom (`{ error: { mensaje|message|detail } }`)

Esto provoca parsing heterogéneo en frontend y pérdida de mensajes útiles.

---

## Convención canónica mínima (v1-operativa)

## Éxito (canónico objetivo)
```json
{
  "exito": true,
  "data": { ... },
  "meta": { "trace_id": "..." }
}
```

## Éxito (compatibilidad temporal aceptada)
- Se acepta también respuesta directa de objeto/array en endpoints legacy.

## Error (canónico objetivo)
```json
{
  "exito": false,
  "error": {
    "code": "...",
    "message": "...",
    "detail": "..."
  }
}
```

## Error (compatibilidad temporal aceptada)
- `detail` (FastAPI)
- `message`
- `mensaje`
- `error.message|error.mensaje|error.detail`

## Naming
- Backend API pública: snake_case (actual predominante).
- Frontend: puede mapear a camelCase en capa de servicio, no en componentes.

## Fechas
- Formato ISO-8601 (UTC cuando aplique) en API.
- Si endpoint legacy envía otro formato, normalizar en servicio frontend antes de UI.

## Números/decimales
- API: números JSON (`number`), evitando strings decimales en campos de negocio nuevos.
- Legacy con strings decimales se tolera temporalmente y se parsea en servicios.

---

## Qué queda canónico vs legacy

## Canónico desde ya
- Parser de errores del cliente HTTP central (`frontend/src/servicios/api.ts`) debe soportar todas variantes.
- Endpoint/servicio nuevo debe priorizar envelope con `exito` + payload consistente.

## Legacy aceptado temporalmente
- Respuestas directas sin `exito`.
- Errores `detail` y `message/mensaje` mezclados.

---

## Criterio de cierre mínimo de prioridad 3
1. Parser central de errores robusto (sin pérdida de `detail/message/mensaje`).
2. Matriz endpoint frontend↔backend actualizada para rutas críticas.
3. Plan de transición incremental que no rompa pantallas actuales.

> Esto **no** equivale a unificación completa de todo el sistema (eso queda fuera del bloque 05).
