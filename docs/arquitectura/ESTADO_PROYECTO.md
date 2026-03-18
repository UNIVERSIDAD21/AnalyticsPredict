# ESTADO_PROYECTO.md

Estado global: EN EJECUCIÓN (pre-lanzamiento comercial)
Última actualización: 2026-03-18
Responsable operativo: UNIVERSIDAD21

## Objetivo actual
Llegar a lanzamiento comercial mínimo viable con capacidad de cobrar el primer peso y operar con trazabilidad.

## Camino crítico vigente
A1 → (A2/A3/A4/A5) → A6 → (B1/B2/B3) → (B4/B5/B6) → B7

## Estado por bloque

| Bloque | Estado | Hecho | Decisiones tomadas | Abierto |
|---|---|---|---|---|
| A1 | EN_CURSO | Plan v3 incorporado, ADRs iniciales creados, CI en GitHub Actions creado (`.github/workflows/ci.yml`), base de staging en Docker creada (`deploy/staging/*`), validación local CI realizada (backend smoke 3/3 y frontend lint/build OK) | Staging+CI/CD básico adelantado a A1 | Validar despliegue real de staging con `staging.env` y smoke operativo (pendiente: host actual sin Docker) |
| A2 | CERRADO | E2E ejecutado en staging: register/login/me/refresh/logout/revocación + forgot/reset por SMTP con MailHog local, login con nueva contraseña OK; backend saludable en `:18000` | Base auth en PostgreSQL + flujo SMTP validado extremo a extremo en entorno desplegado | Opcional posterior: reemplazar MailHog por proveedor SMTP externo (SendGrid/Resend/etc.) sin cambios de código |
| A3 | EN_CURSO | Auth API soporta `v2|legacy` con telemetría + deprecación explícita y frontend auth migrado a `version=v2` (login/register/me/refresh/logout/forgot/reset) con compat fallback | Contrato canónico primero en Auth, luego expansión por dominios; legacy temporal con Sunset | Extender patrón canónico al resto de rutas críticas y activar métricas de adopción para retiro legacy |
| A4 | PENDIENTE | — | Legal transversal obligatorio | Persistencia de aceptación legal |
| A5 | PENDIENTE | — | Métricas mínimas operativas obligatorias | Implementación dashboard/alertas |
| A6 | PENDIENTE | — | Gate con 0 P0/P1 | Validación integral |
| B1 | PENDIENTE | — | MercadoPago como gateway inicial | Implementación checkout/webhooks |
| B2 | PENDIENTE | — | Dashboard de usuario obligatorio para retención | Implementación onboarding+dashboard |
| B3 | PENDIENTE | — | Fútbol cross-liga v1 requerido antes del GO final | Ajustes de features y calibración |
| B4 | PENDIENTE | — | Notificaciones MVP por email | Jobs y preferencias usuario |
| B5 | PENDIENTE | — | Contexto chat con ventana deslizante N | Implementación chat_contexto.py |
| B6 | PENDIENTE | — | Hardening productivo se mantiene en fase B | Infra seguridad y runbooks |
| B7 | PENDIENTE | — | Gate final de salida comercial | E2E primer peso |

## Reglas permanentes de documentación
1. Al cerrar bloque: actualizar este archivo.
2. Registrar entrada breve en `CHANGELOG.md`.
3. Actualizar estado ADR (`PROPUESTO/ACEPTADO/SUPERADO`).
4. Eliminar/archivar documentación obsoleta para evitar contexto viejo.
