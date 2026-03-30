# FASE 1 — Política central de capabilities y tiers

Fecha: 2026-03-30
Estado: CERRADA
Referencia funcional obligatoria: `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`

## Objetivo de la fase
Centralizar la lógica de acceso por capability/tier y eliminar validaciones dispersas en frontend/backend.

## Cambios implementados

### Backend
- Nuevo módulo central: `backend/servicios/access_policy.py`
  - Catálogo único de capabilities vigentes.
  - Registro explícito de capability fuera de alcance (`chat.contextual`).
  - Reglas de tier mínimo por capability.
  - Resolución de gate (`BASE_REQUIRED`, `PREMIUM_REQUIRED`, `DISABLED`).
  - Evaluador estándar `evaluar_capability(...)`.
- Refactor de enforcement: `backend/servicios/access_tiers.py`
  - `exigir_premium(...)` ahora delega en `exigir_capability(..., "premium.depth", ...)`.
  - Nuevo `exigir_capability(...)` con respuestas tipadas 403 por tipo de bloqueo.
- Refactor de rutas access: `backend/api/rutas_access.py`
  - `GET /api/access/capability-check` ahora usa política central y devuelve:
    - `required_tier`
    - `enabled`
    - `gate`
  - Nuevo `GET /api/access/policy` para exponer política vigente de capabilities.

### Frontend
- Refactor de política central: `frontend/src/servicios/accessPolicy.ts`
  - Catálogo único `CAPABILITY_META` (tier mínimo + estado disabled).
  - Resolución estándar de habilitación por tier.
  - Resolución de tipo de gate (`BASE_REQUIRED`, `PREMIUM_REQUIRED`, `DISABLED`).
  - Se mantiene compatibilidad con `construirAccessPolicy`, `puedeAcceder`, `obtenerGateCopy`.

## Cumplimiento explícito contra doc 06
- ✅ Tiers vigentes: Visitante/Base/Premium sin inventar tiers nuevos.
- ✅ Capabilities oficiales incluidas.
- ✅ `chat.contextual` se mantiene fuera de alcance (disabled).
- ✅ Política central para evitar lógica dispersa.
- ✅ Diferenciación funcional de bloqueo Base vs Premium.

## Validación técnica ejecutada
- `python3 -m py_compile backend/servicios/access_policy.py backend/servicios/access_tiers.py backend/api/rutas_access.py backend/api/rutas_premium.py`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`

Todos los comandos terminaron en verde.

## Resultado
Fase 1 cerrada con política central unificada de acceso y enforcement consistente FE/BE, lista para avanzar a Fase 2 (visibilidad y UX de gates).
