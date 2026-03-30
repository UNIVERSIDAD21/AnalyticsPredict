# FASE 2 — Gates UX y visibilidad progresiva por tier

Fecha: 2026-03-30
Estado: CERRADA
Referencia funcional obligatoria: `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`

## Objetivo de la fase
Aplicar un sistema de gates UX consistente con diferenciación clara entre bloqueo Base y bloqueo Premium, copy permitido y comportamiento reutilizable.

## Cambios implementados

### 1) Catálogo de copy y configuración de gates (frontend)
Archivo: `frontend/src/servicios/accessPolicy.ts`

- Se incorporan catálogos explícitos de copy permitido:
  - `COPY_PERMITIDO_BASE`
  - `COPY_PERMITIDO_PREMIUM`
- Se añade `GateConfig` y `obtenerGateConfig(...)` para centralizar:
  - tipo de gate,
  - copy,
  - CTA principal/secundario,
  - destinos de navegación.
- Se mantiene `chat.contextual` como capability deshabilitada (`DISABLED`).

### 2) Diferenciación visual/semántica de bloqueo Base vs Premium
Archivo: `frontend/src/contextos/GatePromptContext.tsx`

- El gate modal ahora recibe `tipoGate`.
- Se implementa estilo diferenciado por tipo:
  - `BASE_REQUIRED` → “Bloqueo de cuenta” (enfoque continuidad personal).
  - `PREMIUM_REQUIRED` → “Bloqueo Premium” (enfoque profundidad operativa).
  - `DISABLED` → “Fuera de alcance”.
- Se adapta iconografía, mensaje de ayuda y acento visual por tipo de bloqueo.

### 3) Hook de navegación con gates centralizados
Archivo: `frontend/src/hooks/useGateNavigation.ts`

- Se deja de armar manualmente CTA y rutas por cada caso.
- Se consume `obtenerGateConfig(...)` para comportamiento uniforme.
- `gate_blocked` ahora registra `gateType` en analítica de producto.

## Cumplimiento explícito contra doc 06

- ✅ Diferencia explícita entre bloqueo Base y bloqueo Premium (sección 7.8, 15.6).
- ✅ Bloqueo educa y explica valor, no solo niega acceso (sección 8.3).
- ✅ CTA y copy alineados a listas permitidas (sección 8 + anexo B).
- ✅ Chat permanece fuera de alcance (sección 12).
- ✅ Progresión visible sin redirecciones agresivas directas desde la entrada pública.

## Validación técnica ejecutada

- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`

Ambos comandos finalizaron en verde.

## Resultado
Fase 2 cerrada con gates UX reutilizables, diferenciación Base/Premium y centralización de copy/CTA para todo el frontend.
