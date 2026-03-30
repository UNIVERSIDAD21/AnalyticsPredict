# FASE 3 — Header y navegación global tier-aware

Fecha: 2026-03-30
Estado: CERRADA
Referencia funcional obligatoria: `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`

## Objetivo de la fase
Alinear el encabezado y la navegación global al modelo de tiers para que el acceso ocurra por acción protegida con contexto, manteniendo coherencia entre Visitante, Base y Premium.

## Cambios implementados

### Encabezado global tier-aware
Archivo: `frontend/src/componentes/organismos/Encabezado.tsx`

- Se integra lectura de tier real desde `useAccessPolicy()`.
- Se agrega indicador visible de estado de cuenta:
  - Visitante: `Modo visitante`
  - Base: `Cuenta base`
  - Premium: `Premium activo`
- Se corrige navegación de dashboard para ambos deportes:
  - NBA: `/dashboard`
  - Fútbol: `/futbol/dashboard`
- Se corrige marcado activo de dashboard por deporte (evita estado falso cuando se está en NBA).
- Se consolida acceso al centro público en `/` (sin depender del alias legacy).
- El CTA visitante del header se mantiene como acción protegida (gate contextual), no redirección agresiva.

## Cumplimiento explícito contra doc 06

- ✅ Header responde al sistema de tiers (sección 13.1).
- ✅ Visitante ve navegación y progresión, con gate por acción (sección 13.2 + 3.4).
- ✅ Base/Premium mantienen navegación operativa real (sección 13.3/13.4).
- ✅ Botón de desbloqueo para visitante con contexto, no login forzado sin intento (sección 13.5).
- ✅ Indicador Demo/Bankroll permanece visible como estado operativo (sección 13.6).

## Validación técnica ejecutada

- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`

Ambos comandos finalizaron en verde.

## Resultado
Fase 3 cerrada con navegación global coherente por tier, corrección de flujo dashboard NBA/Fútbol y señalización de estado de cuenta en header.
