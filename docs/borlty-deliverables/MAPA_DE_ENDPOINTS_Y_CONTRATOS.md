# MAPA_DE_ENDPOINTS_Y_CONTRATOS.md

## Resumen

Se mapearon endpoints backend y consumo real frontend para detectar desalineaciones contractuales.

- Endpoints backend detectados: **79**
- Rutas API consumidas por frontend: **34**
- Inconsistencias críticas detectadas: **1 endpoint consumido por frontend no encontrado en backend**

---

## 1) Endpoints principales backend por dominio

## Núcleo/Sistema
- `GET /`
- `GET /salud`

## NBA (análisis y operación)
- `POST /api/analizar`
- `POST /api/analizar-en-vivo`
- `GET /api/partidos`
- `GET /api/partidos/hoy`
- `GET /api/partidos/proximos`
- `GET /api/partidos/{partido_id}`
- `GET /api/predicciones/historial`
- `POST /api/bitacora`
- `GET /api/bitacora`
- `GET /api/bitacora/resumen`
- `PATCH /api/bitacora/{apuesta_id}/resultado`
- `DELETE /api/bitacora/{apuesta_id}`
- `POST /api/bitacora/resolver`

## Fútbol
- `POST /api/futbol/analizar`
- `GET /api/futbol/partidos/hoy|proximos|recientes|h2h|{partido_id}`
- `GET /api/futbol/competiciones`
- `GET /api/futbol/equipos`
- `POST /api/futbol/apuestas`
- `GET /api/futbol/apuestas`
- `GET /api/futbol/apuestas/{apuesta_id}`
- `PATCH /api/futbol/apuestas/{apuesta_id}`
- `DELETE /api/futbol/apuestas/{apuesta_id}`
- `POST /api/futbol/apuestas/resolver`

## Métricas
- `GET /api/metricas/*`
- `GET /api/futbol/metricas/*`

## Interno/operación
- `POST /api/interno/recalibrar`
- `POST /api/interno/resolver-predicciones`
- `POST /api/interno/resolver-predicciones-futbol`
- `GET /api/interno/alertas-calibracion`
- `POST /api/interno/alertas-calibracion/resolver`

---

## 2) Endpoints consumidos por frontend (observado en `frontend/src/servicios/*`)

- `/api/analizar`
- `/api/analizar-en-vivo`
- `/api/bitacora`
- `/api/bitacora/resumen`
- `/api/bitacora/metricas`
- `/api/bitacora/apuestas-analizadas`
- `/api/bitacora/unificada`
- `/api/combinadas`
- `/api/equipos`
- `/api/equipos/temporadas`
- `/api/estadisticas-equipos`
- `/api/partidos`
- `/api/partidos/hoy`
- `/api/partidos/proximos`
- `/api/partidos/buscar`
- `/api/predicciones/historial`
- `/api/metricas/calibracion`
- `/api/interno/recalibrar`
- `/api/interno/alertas-calibracion/resolver`
- `/api/futbol/analizar`
- `/api/futbol/partidos/hoy|proximos|recientes|h2h`
- `/api/futbol/competiciones`
- `/api/futbol/equipos`
- `/api/futbol/apuestas`
- `/api/futbol/apuestas/resolver`
- `/api/futbol/apuestas/estadisticas` ⚠️
- `/api/futbol/metricas/resumen|rendimiento|calibracion|modelos|resumen-calidad-1x2`

---

## 3) Inconsistencias contrato backend/frontend

## Crítica
1. **Frontend consume `/api/futbol/apuestas/estadisticas` pero backend no expone esa ruta.**
   - Efecto: error en runtime para paneles/estadísticas de apuestas fútbol.

## Alta
2. **Envelope de respuesta no homogéneo**
   - Algunos servicios frontend esperan `{ exito, ... }`.
   - Varias rutas backend retornan objeto directo (sin `exito`).

3. **Formato de error no homogéneo**
   - Frontend (`extraerMensajeError`) prioriza `error.mensaje`.
   - Backend FastAPI frecuentemente responde `detail`.
   - Resultado: mensajes genéricos en UI aunque backend envíe detalle útil.

## Media
4. **Naming mixto snake_case/camelCase entre capas**
   - Hay transformadores manuales en frontend para mitigar.
   - Aumenta deuda de mantenimiento y riesgo de campos huérfanos.

5. **Estados/confianza con semántica distinta por dominio**
   - NBA usa patrón `ALTA/MEDIA/BAJA`.
   - Fútbol expone también `MUY_ALTA/MUY_BAJA` en algunos contratos.

---

## 4) Payloads de éxito (patrones actuales)

## Patrón A — Envelope explícito
```json
{
  "exito": true,
  "total": 123,
  "resumen": { ... },
  "apuestas": [ ... ]
}
```

## Patrón B — Objeto directo de recurso
```json
{
  "id": "...",
  "mercado": "...",
  "stake": 100,
  "...": "..."
}
```

## Riesgo
El frontend debe conocer endpoint por endpoint qué patrón usar, lo que rompe estandarización.

---

## 5) Payloads de error (patrones actuales)

## Patrón observado 1 — FastAPI estándar
```json
{ "detail": "mensaje" }
```

## Patrón observado 2 — Envelope custom
```json
{
  "error": {
    "code": "...",
    "message": "...",
    "detail": "...",
    "trace_id": "..."
  }
}
```

## Riesgo
Frontend no siempre parsea ambos de forma uniforme; puede degradar UX y trazabilidad de incidentes.

---

## 6) Propuesta preliminar de unificación (sin implementar aún)

1. **Contrato único de éxito** (envelope estándar):
```json
{
  "ok": true,
  "data": { ... },
  "meta": { "trace_id": "...", "version": "v1" }
}
```

2. **Contrato único de error**:
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "...",
    "details": { ... },
    "trace_id": "..."
  }
}
```

3. **Naming canónico por capa**
- Backend: snake_case interno.
- API pública: definir uno solo (ideal: snake_case si backend ya está en ese estándar).
- Frontend: transformar en un único sitio (cliente HTTP), no en múltiples servicios.

4. **Matriz contrato endpoint↔frontend**
- Crear archivo de verificación por endpoint consumido para evitar rutas huérfanas.

---

## 7) Acciones mínimas prioritarias derivadas de este mapa

1. Resolver ruta faltante `/api/futbol/apuestas/estadisticas` (crear o ajustar frontend).
2. Unificar parseo de errores en `frontend/src/servicios/api.ts` (`detail|message|mensaje`).
3. Definir y documentar envelope único de respuestas.
4. Crear test de contrato (smoke) que compare rutas backend vs rutas consumidas frontend.
