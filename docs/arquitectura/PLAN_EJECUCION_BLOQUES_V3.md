# Plan de Ejecución por Bloques v3 (Ingeniería Ejecutable)

Estado: ACTIVO
Última actualización: 2026-03-18

## Camino crítico
A1 → (A2/A3/A4/A5 en paralelo) → A6 → (B1/B2/B3 en paralelo) → (B4/B5/B6 en paralelo parcial) → B7

## Regla de cierre documental (obligatoria)
Al cerrar cada bloque:
1. Actualizar `docs/arquitectura/ESTADO_PROYECTO.md`
2. Agregar entrada en `CHANGELOG.md`
3. Actualizar estado de ADRs: `PROPUESTO` / `ACEPTADO` / `SUPERADO`
4. Archivar o eliminar documentos obsoletos

---

## Fase A (base técnica y comercial)

### A1 — Baseline técnico + staging + CI/CD básico
**Objetivo:** definir arquitectura base y habilitar ambiente de pruebas desde el día 1.

**Tareas técnicas concretas:**
- ADRs iniciales: auth, pagos, notificaciones/chat contexto.
- Crear staging funcional (URL separada, variables de entorno, DB de staging).
- Pipeline CI básico: lint + tests + build + deploy staging.
- Definir checklist de salida por bloque.

**Dependencias:** inicio.

**Bloque cerrado cuando:**
- ADRs base publicados.
- Staging operativo y accesible.
- CI corriendo en cada push/PR.

**Estimado:** 2–3 días.

### A2 — Autenticación real + recuperación de contraseña
**Objetivo:** reemplazar flujo dev por auth comercial segura.

**Tareas técnicas concretas:**
- Endpoints `register/login/refresh/logout/forgot/reset`.
- Hash de contraseñas y manejo de tokens con expiración.
- Rutas protegidas en API y frontend.
- E2E de sesión completa.

**Dependencias:** A1.

**Bloque cerrado cuando:**
- E2E auth pasa en staging.
- No se puede consumir ruta protegida sin token válido.

**Estimado:** 6–8 días.

### A3 — Contrato canónico + deprecación legacy
**Objetivo:** eliminar incoherencias de contrato backend/frontend.

**Tareas técnicas concretas:**
- Normalizar respuestas canónicas.
- Mantener capa legacy temporal con telemetría.
- Marcar deprecación explícita.

**Dependencias:** A1.

**Bloque cerrado cuando:**
- Front consume contrato canónico sin parches ad-hoc.
- Telemetría de legacy activa.

**Estimado:** 4–6 días.

### A4 — Legal transversal mínimo
**Objetivo:** cobertura legal obligatoria en todo flujo relevante.

**Tareas técnicas concretas:**
- Páginas T&C, Privacidad y Disclaimer.
- Registro de aceptación de versión legal por usuario.
- UI de aceptación previa al uso.

**Dependencias:** A1.

**Bloque cerrado cuando:**
- Ningún flujo crítico opera sin aceptación legal.

**Estimado:** 2–4 días.

### A5 — Observabilidad operativa mínima
**Objetivo:** detectar y diagnosticar incidentes rápido.

**Tareas técnicas concretas:**
- Logs estructurados con trace_id/request_id.
- Métricas p95, error rate, uptime, scraping health.
- Alertas automáticas por umbral.

**Dependencias:** A1.

**Bloque cerrado cuando:**
- Dashboard operativo mínimo disponible.
- Alertas validadas en prueba controlada.

**Estimado:** 4–5 días.

### A6 — Gate Fase A
**Objetivo:** no pasar a monetización con deuda bloqueante.

**Tareas técnicas concretas:**
- Validación integral A2/A3/A4/A5 en staging.
- Cierre de P0/P1.

**Dependencias:** A2+A3+A4+A5.

**Bloque cerrado cuando:**
- 0 bloqueantes P0/P1.
- RC-A aprobado.

**Estimado:** 2 días.

---

## Fase B (primer peso + retención)

### B1 — Pagos y suscripción E2E (MercadoPago)
**Objetivo:** cobrar el primer peso.

**Tareas técnicas concretas:**
- Checkout + webhook firmado + reconciliación.
- Estado de suscripción y feature gating.

**Dependencias:** A6.

**Bloque cerrado cuando:**
- Pago real activa plan y se refleja en permisos.

**Estimado:** 7–10 días.

### B2 — Onboarding + dashboard usuario
**Objetivo:** convertir y retener usuario.

**Tareas técnicas concretas:**
- Wizard onboarding.
- Dashboard con historial, rendimiento y estado de plan.

**Dependencias:** A6.

**Bloque cerrado cuando:**
- Usuario nuevo completa onboarding y entiende valor.

**Estimado:** 5–7 días.

### B3 — Estabilización fútbol + cross-liga v1
**Objetivo:** mejorar robustez predictiva de fútbol para operación comercial.

**Tareas técnicas concretas:**
- Features cross-liga ponderadas.
- Ajuste confianza con muestra total/relevante.
- Policy gate por drift/calidad.

**Dependencias:** A6.

**Bloque cerrado cuando:**
- 2 ciclos semanales sin degradación crítica sostenida.

**Estimado:** 8–10 días.

### B4 — Notificaciones (MVP)
**Objetivo:** activar retorno del usuario.

**Tareas técnicas concretas:**
- Alertas por email para partidos relevantes y eventos de suscripción.
- Preferencias por usuario.

**Dependencias:** B1 + B2.

**Bloque cerrado cuando:**
- Alertas salen con trazabilidad y opt-out funcional.

**Estimado:** 3–4 días.

### B5 — Chatbot contextual MVP (con control de costo)
**Objetivo:** soporte/valor diferencial sin inflación de tokens.

**Tareas técnicas concretas:**
- `POST /api/chat` con contexto del usuario.
- `chat_contexto.py` con ventana deslizante de últimos **N** registros relevantes (no historial completo).
- Guardrails de riesgo/disclaimer.

**Dependencias:** B2.

**Bloque cerrado cuando:**
- Responde preguntas clave usando solo contexto acotado.
- Costo por request dentro del umbral definido.

**Estimado:** 4–6 días.

### B6 — Hardening productivo (no staging)
**Objetivo:** seguridad y resiliencia para producción real.

**Tareas técnicas concretas:**
- Hardening de infraestructura y secretos.
- Backups + restore test.
- Runbook de incidentes y rollback.

**Dependencias:** A1 (base ya hecha), ejecución final con B1/B2/B3 avanzados.

**Bloque cerrado cuando:**
- Auditoría de seguridad operativa mínima aprobada.

**Estimado:** 4–6 días.

### B7 — Gate final de lanzamiento comercial
**Objetivo:** validar flujo completo de monetización.

**Tareas técnicas concretas:**
- E2E: registro → onboarding → pago → uso premium → notificación.
- Cierre de defectos críticos.

**Dependencias:** B1+B2+B3+B4+B5+B6.

**Bloque cerrado cuando:**
- Flujo “primer peso” validado extremo a extremo sin P0/P1.

**Estimado:** 2–3 días.
