# PLAN DE EJECUCIÓN — ACCESO POR TIER, MODO VISITANTE Y CAPA PREMIUM

Fecha: 2026-03-27
Estado: ACTIVO (fase de implementación)
Avance actual: Fase A→F cerradas (incluye Fase F con copy final, instrumentación de eventos de producto y checklist de aceptación final)
Referencia funcional base: `docs/roadmap_inmediato/inputs_producto/ACCESO_POR_TIER_MODO_VISITANTE_Y_CAPA_PREMIUM.md`

---

## 0) Decisión de alcance vigente (obligatoria)

- **Chat queda fuera de alcance en fase actual**.
- Debe permanecer oculto en UI y deshabilitado en backend hasta instrucción explícita.
- Todo el plan de abajo asume chat = fase futura.

---

## 1) Objetivo de ejecución

Aterrizar la arquitectura de acceso por tiers en producto real, cumpliendo:

1. `/` como modo visitante del sistema (no landing aislada).
2. Matriz funcional cerrada Visitante / Base / Premium.
3. Gates por acción (no solo por ruta).
4. Premium definido por profundidad real, no por bloquear lo básico.
5. Gobernanza por deporte visible y honesta.

---

## 2) Fases, entregables y criterio de cierre

## Fase A — Política central de acceso (backend + frontend)

### Entregables
- Módulo central de policy de acceso por capacidades, por ejemplo:
  - `frontend/src/servicios/accessPolicy.ts`
  - `backend/servicios/access_policy.py` (si aplica para enforcement server-side)
- Catálogo único de capacidades:
  - `can_view_public_center`
  - `can_run_full_nba_analysis`
  - `can_open_personal_dashboard`
  - `can_use_bitacora`
  - `can_view_premium_depth`
  - etc.
- Mapeo capability → tier (`VISITANTE`, `BASE`, `PREMIUM`).

### Cierre
- No hay validaciones dispersas de acceso por pantalla suelta sin pasar por policy.

---

## Fase B — Entrada principal y shell visitante

### Entregables
- `/` se consolida como shell visitante real.
- Integrar en esa entrada:
  - centro analítico público,
  - selector de deporte,
  - gobernanza por madurez,
  - snapshots públicos (2-4 bloques máximo).
- La landing previa se absorbe como bloque contextual dentro del shell.

### Cierre
- Un visitante entiende valor sin login y percibe producto operativo real.

---

## Fase C — Gates por acción y UX de conversión

### Entregables
- Definir acciones protegidas y su gate:
  - abrir análisis profundo,
  - guardar en bitácora,
  - abrir dashboard/configuración,
  - abrir capas premium.
- Componente de gate reutilizable (modal/panel):
  - CTA registro/login,
  - copy funcional y no agresivo,
  - trazabilidad de evento.

### Cierre
- No se bloquea la exploración pública; se bloquea solo la continuidad personal/profundidad.

---

## Fase D — Separación Base vs Premium

### Entregables
- Definir y aplicar “capas premium” dentro de módulos existentes:
  - comparativas avanzadas,
  - profundidad histórica,
  - paneles extendidos,
  - alertas avanzadas (sin chat en esta fase).
- Mantener completo el flujo base:
  - analizar,
  - bitácora,
  - dashboard,
  - configuración,
  - onboarding.

### Cierre
- Base útil y completo; premium claramente superior por profundidad.

---

## Fase E — Routing y hardening de acceso

### Entregables
- Normalizar rutas:
  - públicas (`/`, `/login`, `/legal/*`, etc.),
  - protegidas base,
  - premium por capa (no necesariamente por ruta).
- Enforcement backend para acciones críticas con verificación de suscripción/tier.
- Auditoría de bypass (frontend + backend).

### Cierre
- No existen caminos alternos para ejecutar acciones fuera de tier.

---

## Fase F — Copy, instrumentación y aceptación

### Entregables
- Copy final por tier (visitante/base/premium) alineado al MD.
- Eventos de analítica de producto:
  - vista pública,
  - intentos de acción protegida,
  - conversión a registro,
  - uso de capa premium.
- Checklist final contra criterios del documento de tiers.

### Cierre
- Cumplimiento formal de criterios de aceptación (sección 21 del MD de tiers).

---

## 3) Orden de ejecución técnico recomendado (secuencial)

1. Fase A (policy central)
2. Fase B (entrada `/` visitante)
3. Fase C (gates por acción)
4. Fase D (capas premium)
5. Fase E (hardening access)
6. Fase F (copy + métricas + cierre)

---

## 4) Definición de “hecho” por bloque

Cada fase se cierra solo si incluye:
- cambios en código,
- validación técnica (lint/build/tests según aplique),
- actualización de `docs/arquitectura/ESTADO_PROYECTO.md`,
- entrada en `CHANGELOG.md`,
- evidencia breve en `docs/reportes/` si corresponde.

---

## 5) Riesgos y controles

- Riesgo: romper UX base al introducir premium.
  - Control: tests de navegación base + revisión de flujos críticos.
- Riesgo: copy ambiguo y gates invasivos.
  - Control: catálogo central de mensajes de gate + revisión de tono.
- Riesgo: bypass por endpoints no protegidos.
  - Control: enforcement backend por capability/tier en acciones críticas.

---

## 6) Estado inicial al arrancar este plan

- Documento de tiers ya reubicado y activo en roadmap.
- Chat fuera de alcance actual (UI oculta + backend deshabilitable por flag).
- Próximo bloque sugerido para ejecución inmediata: **Fase A (policy central)**.
