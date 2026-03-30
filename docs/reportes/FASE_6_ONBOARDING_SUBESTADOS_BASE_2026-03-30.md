# FASE 6 — Subestados operativos del tier Base (onboarding incompleto/completo)

Fecha: 2026-03-30
Estado: CERRADA
Referencia funcional obligatoria: `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`

## Objetivo de fase
Aterrizar el subestado del tier Base para que:
- Base con onboarding incompleto sea guiado formalmente,
- Base con onboarding completo opere sin fricción,
- la continuidad del flujo respete la intención del usuario.

## Cambios implementados

### 1) Redirección a onboarding conserva contexto de destino
- Archivo: `frontend/src/App.tsx`
- `RutaConOnboarding` ahora redirige con estado `from` hacia `/onboarding` cuando detecta Base sin onboarding completo.
- Resultado: no se pierde la intención de navegación original del usuario.

### 2) Onboarding finaliza retornando al destino original
- Archivo: `frontend/src/componentes/paginas/PaginaOnboarding.tsx`
- Se incorpora `useLocation` + `useNavigate`.
- Al completar onboarding, el usuario vuelve a la ruta original (`from.pathname`) y, si no existe, cae en `/dashboard`.
- Se ajusta mensaje de éxito para reflejar activación operativa del perfil Base.

### 3) UX explícita del subestado Base incompleto
- Archivo: `frontend/src/componentes/paginas/PaginaOnboarding.tsx`
- Se agrega aviso contextual cuando onboarding fue forzado por intento de acceso a ruta protegida:
  - informa que al terminar volverá al módulo que intentaba abrir.

## Cumplimiento explícito contra doc 06
- ✅ Base autenticado sin onboarding completo: guiado formal antes de operar rutas protegidas dependientes de contexto.
- ✅ Base autenticado con onboarding completo: operación normal con continuidad.
- ✅ Onboarding como etapa real de activación, no adorno visual.

## Validación técnica
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`

Ambos en verde.

## Resultado
Fase 6 cerrada con subestados Base implementados end-to-end: guía obligatoria al onboarding, retorno al flujo original y activación operativa sin fricción tras completarlo.
