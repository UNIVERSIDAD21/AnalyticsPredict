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
| A3 | CERRADO | Auth API en `v2` por defecto + telemetría (`/api/auth/contract-usage`), Bitácora con cobertura `v2|legacy` en endpoints de consulta/operación + telemetría (`/api/bitacora/contract-usage`) y Resolución de apuestas fútbol (`POST /api/futbol/apuestas/resolver`) ya versionada con telemetría (`GET /api/futbol/apuestas/contract-usage`) | Umbral global de sunset formalizado: desactivar legacy cuando ratio legacy <5% por 7 días corridos y ejecutar aviso previo de 30 días | Monitorear métricas de adopción y ejecutar retiro de legacy según umbral ADR |
| A4 | CERRADO | Registro exige aceptación legal versionada y persistida; endpoint autenticado `POST /api/auth/accept-legal` para regularizar usuarios legacy; guard legal activo en `login/refresh/me/logout` bloqueando operación con `LEGAL_REACCEPT_REQUIRED` cuando `legal_accepted_version` no coincide con vigente | Legal transversal obligatorio con versionado explícito y reaceptación forzada por versión | Opcional posterior: extender guard legal a dominios legacy con auth por `X-Usuario-Id` hasta completar migración a auth unificada |
| A5 | CERRADO | Instrumentación HTTP mínima en backend + integración en dashboard operativo (`/salud` + `/api/interno/observabilidad-http`) con tarjetas de estado p95/error rate/alertas; pruebas endpoint para esquema y disparo controlado de alertas (`backend/tests/test_observabilidad_http_endpoint.py`) | Métricas mínimas operativas obligatorias con visualización y validación automatizada | Opcional posterior: exportar observabilidad a almacenamiento persistente (Prometheus/Grafana) para histórico > reinicio de proceso |
| A6 | CERRADO | Gate RC-A ejecutado con script operativo `scripts/validar_a6_rca.sh`; evidencia en `docs/reportes/A6_RC-A_2026-03-18T07-28-30Z.md` con backend (21 tests) + frontend lint/build en verde | Gate con 0 P0/P1 | Mantener corrida RC-A en cada avance crítico de B1/B2/B3 para evitar regresión antes de monetización |
| B1 | EN_CURSO | Backend B1 base implementado: `POST /api/pagos/checkout-session`, `POST /api/pagos/webhook/mercadopago` (firma HMAC), `GET /api/pagos/suscripcion/mia`, `GET /api/pagos/feature-gate`; store SQLite de intents/suscripciones (`backend/servicios/pagos_store.py`) + pruebas API (`backend/tests/api/test_pagos_endpoints.py` 3/3) | MercadoPago como gateway inicial | Conectar SDK/credenciales reales de MercadoPago y reconciliación de eventos productivos (hoy está en modo sandbox/contrato interno) |
| B2 | EN_CURSO | Onboarding inicial en frontend (`/onboarding`) con wizard de 3 pasos y persistencia por usuario en localStorage (`frontend/src/servicios/onboarding.ts`); dashboard de usuario (`/dashboard`) con resumen de rendimiento (bitácora analizada) + estado de plan (`/api/pagos/suscripcion/mia`) | Onboarding obligatorio antes de uso de rutas principales para guiar activación temprana | Falta persistencia backend del onboarding (hoy localStorage), instrumentar eventos de conversión y cerrar copy/UX final de retención |
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
