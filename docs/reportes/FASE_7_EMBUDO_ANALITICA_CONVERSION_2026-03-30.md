# FASE 7 — Embudo y analítica de conversión

Fecha: 2026-03-30
Estado: CERRADA
Referencia funcional obligatoria: `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`

## Objetivo
Instrumentar el embudo oficial (explorar → registro/base → onboarding → consumo base → intento premium) con eventos consistentes y trazables.

## Cambios implementados

### 1) Evento de vista del centro público normalizado
- Archivo: `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx`
- Se conserva `public_center_view` y se agrega `public_center_viewed` para normalizar naming del embudo.

### 2) Onboarding conectado a analítica de producto del embudo
- Archivo: `frontend/src/componentes/paginas/PaginaOnboarding.tsx`
- Además de telemetría onboarding existente, ahora se registra en product analytics:
  - `onboarding_started`
  - `onboarding_completed`
- Ambos eventos incluyen metadata de destino para medir continuidad de flujo.

### 3) Inicio de consumo Base medible desde auth
- Archivo: `frontend/src/componentes/paginas/PaginaLogin.tsx`
- Al login/registro exitoso se registra:
  - `base_consumption_started`
- Incluye metadata `via` (`login` o `register`) y `destino`.

### 4) Interacción con capas premium y intento de activación
- Archivo: `frontend/src/componentes/moleculas/PanelDepthPremium.tsx`
- Se agrega instrumentación:
  - `premium_layer_interaction` con `interaction=view`
  - `premium_layer_interaction` con `interaction=click_cta`
- Incluye `modulo` (`nba|futbol|futbol_partido`) y estado premium activo.

- Archivo: `frontend/src/hooks/useGateNavigation.ts`
- Al navegar contra capability `premium.depth` se registra:
  - `premium_activation_intent`
- Incluye `ruta`, `autenticado` y `tier`.

### 5) Integración del módulo de profundidad por contexto
- Archivos:
  - `frontend/src/componentes/paginas/PaginaPrincipal.tsx`
  - `frontend/src/componentes/paginas/PaginaFutbol.tsx`
  - `frontend/src/componentes/paginas/AnalisisPartidoFutbol.tsx`
- Se pasa `modulo` al panel premium para atribuir conversiones por superficie.

## Eventos mínimos del embudo cubiertos
- `public_center_viewed` ✅
- `gate_blocked` ✅
- `gate_allowed` ✅
- `onboarding_started` ✅
- `onboarding_completed` ✅
- `premium_layer_interaction` ✅
- `premium_activation_intent` ✅

## Validación técnica
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`

Ambos comandos en verde.

## Resultado
Fase 7 cerrada con embudo instrumentado end-to-end y eventos clave listos para análisis de conversión por tier y por módulo.
