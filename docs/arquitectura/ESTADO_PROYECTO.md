# ESTADO_PROYECTO.md

Estado global: EN EJECUCIÓN (pre-lanzamiento comercial)
Última actualización: 2026-03-26 (Ola 1 cerrada + Ola 2 en ejecución)
Responsable operativo: UNIVERSIDAD21

## Objetivo actual
Llegar a lanzamiento comercial mínimo viable con capacidad de cobrar el primer peso y operar con trazabilidad.

## Prioridad comercial complementaria (vigente)
Se activa ejecución por olas del plan público P1–P9:
- Ola 1: P1 Credibilidad, P2 Freemium/límites, P3 Propuesta de valor.
- Ola 2: P4 Fútbol sin maquillaje, P6 Visibilidad inteligencia, P8 Premium.
- Ola 3: P7 Mejora de motor/modelo, P9 UX y rendimiento.

## Estado plan público P1–P9 (producto/comercial)
- Ola 1 (P1/P2/P3): CERRADA en front principal (landing + centro analítico + acceso visitante limitado).
- Ola 2 (P4/P6/P8): CERRADA con implementación transversal en landing, centro analítico, dashboard, login y configuración; con umbrales de promoción fútbol y matriz funcional premium consolidada.
- Ola 3 (P7/P9): CERRADA en alcance frontend/producto con baseline operativo, optimizaciones de carga, métricas cliente visibles y benchmark documentado.

## Camino crítico vigente (realineado por C0)
C0 → C1 → C2 → C3 → C4 → C7

## Camino paralelo controlado (no bloqueante de primer peso)
C5 → C6

## Nota de transición
El esquema A/B queda como histórico de ejecución previa. Para decisiones de lanzamiento comercial rige la secuencia C0–C7 y ADR-005.

## Estado rápido C0–C7 (go-live comercial)
- C0: CERRADO
- C1: EN_CURSO (pendiente validación manual final de MP; bloqueado hasta contar con dominio/URL pública para webhook real en entorno de lanzamiento)
- C2: CERRADO
- C3: CERRADO
- C4: CERRADO
- C5: CERRADO
- C6: CERRADO
- C7: PENDIENTE

## Preflight C7 (condición de apertura)
- C7 NO se abre hasta cierre manual real de C1 por el dueño.
- Bloqueo actual C1: falta dominio/URL pública final para validar webhook real de MercadoPago extremo a extremo.
- Al desbloquear infraestructura (dominio + callback pública estable), ejecutar cierre manual C1 con evidencia y recién después abrir C7.
- Nota de gobierno: ninguna mejora de olas P1–P9 reemplaza este prerequisito comercial.

## Regla documental de validación C1 (normalizada)
- **Validación equivalente reproducible** (tests/pytest): readiness técnico.
- **Validación manual homologada** (sandbox/homologación oficial): prevalidación manual.
- **Validación manual real** (cobro real en entorno final): única que habilita C1=CERRADO y apertura de C7.

## Nota de nomenclatura C vs B (para reducir confusión)
- C0–C7 gobierna la ruta comercial de lanzamiento.
- B1–B7 conserva trazabilidad histórica de implementación por capacidades.
- En pagos, la correspondencia vigente es: **C1 (bloque comercial) ⇄ B1 (implementación técnica de pagos)**.

## Estado por bloque

| Bloque | Estado | Hecho | Decisiones tomadas | Abierto |
|---|---|---|---|---|
| A1 | CERRADO | Plan v3 incorporado, ADRs iniciales creados, CI en GitHub Actions creado (`.github/workflows/ci.yml`), base de staging en Docker creada (`deploy/staging/*`), despliegue real en host con `docker compose --env-file staging.env up -d --build` y smoke operativo exitoso (`docs/reportes/A1_SMOKE_STAGING_2026-03-26T14:12:43Z.md`) | A1 queda formalmente cerrado con staging reproducible + evidencia de servicios activos y smoke E2E mínimo | Seguimiento operativo no bloqueante: mantener smoke A1 en cada cambio de infraestructura o dependencias base |
| A2 | CERRADO | E2E ejecutado en staging: register/login/me/refresh/logout/revocación + forgot/reset por SMTP con MailHog local, login con nueva contraseña OK; backend saludable en `:18000` | Base auth en PostgreSQL + flujo SMTP validado extremo a extremo en entorno desplegado | Opcional posterior: reemplazar MailHog por proveedor SMTP externo (SendGrid/Resend/etc.) sin cambios de código |
| A3 | CERRADO | Auth API en `v2` por defecto + telemetría (`/api/auth/contract-usage`), Bitácora con cobertura `v2|legacy` en endpoints de consulta/operación + telemetría (`/api/bitacora/contract-usage`) y Resolución de apuestas fútbol (`POST /api/futbol/apuestas/resolver`) ya versionada con telemetría (`GET /api/futbol/apuestas/contract-usage`) | Umbral global de sunset formalizado: desactivar legacy cuando ratio legacy <5% por 7 días corridos y ejecutar aviso previo de 30 días | Monitorear métricas de adopción y ejecutar retiro de legacy según umbral ADR |
| A4 | CERRADO | Registro exige aceptación legal versionada y persistida; endpoint autenticado `POST /api/auth/accept-legal` para regularizar usuarios legacy; guard legal activo en `login/refresh/me/logout` bloqueando operación con `LEGAL_REACCEPT_REQUIRED` cuando `legal_accepted_version` no coincide con vigente | Legal transversal obligatorio con versionado explícito y reaceptación forzada por versión | Opcional posterior: extender guard legal a dominios legacy con auth por `X-Usuario-Id` hasta completar migración a auth unificada |
| A5 | CERRADO | Instrumentación HTTP mínima en backend + integración en dashboard operativo (`/salud` + `/api/interno/observabilidad-http`) con tarjetas de estado p95/error rate/alertas; pruebas endpoint para esquema y disparo controlado de alertas (`backend/tests/test_observabilidad_http_endpoint.py`) | Métricas mínimas operativas obligatorias con visualización y validación automatizada | Opcional posterior: exportar observabilidad a almacenamiento persistente (Prometheus/Grafana) para histórico > reinicio de proceso |
| A6 | CERRADO | Gate RC-A ejecutado con script operativo `scripts/validar_a6_rca.sh`; evidencia en `docs/reportes/A6_RC-A_2026-03-18T07-28-30Z.md` con backend (21 tests) + frontend lint/build en verde | Gate con 0 P0/P1 | Mantener corrida RC-A en cada avance crítico de B1/B2/B3 para evitar regresión antes de monetización |
| B1 | EN_CURSO (listo para validación manual final C1) | Checkout + webhook idempotente + matriz de estados + feature-gate consistente por suscripción. Webhook actualizado para flujo real de Mercado Pago: validación `X-Signature` (`ts/v1` + `X-Request-Id` + `data.id`), consulta de pago real en `/v1/payments/{id}` para resolver `external_reference`/estado final y persistencia de evento compuesto (`webhook + payment`). Endpoints: `POST /api/pagos/checkout-session`, `POST /api/pagos/webhook/mercadopago`, `GET /api/pagos/suscripcion/mia`, `GET /api/pagos/feature-gate`, `GET /api/pagos/matriz-estados`. Evidencia técnica equivalente en `docs/reportes/C1_E2E_PRIMER_PAGO_VALIDACION_EQUIVALENTE_2026-03-24.md` (6/6) y template de cierre manual en `docs/reportes/C1_CIERRE_MANUAL_MERCADOPAGO_TEMPLATE.md`. | MercadoPago gateway operando sobre evento real con idempotencia por (`external_reference`,`payment_id`,`status`) y activación de suscripción condicionada al estado efectivo del pago | Pendiente validación manual real del dueño: configurar webhook en panel MP, ejecutar E2E real y cerrar C1 con evidencia final |
| B2 | CERRADO | Onboarding y dashboard operativos: wizard frontend (`/onboarding`) + dashboard (`/dashboard`) con persistencia backend `POST/GET /api/onboarding/perfil|estado`, telemetría de conversión (`POST /api/onboarding/evento`) y KPIs reales en API/UI (`GET /api/onboarding/kpis`: completion rate + time-to-value promedio) | Se define B2 como cerrado con criterio de activación instrumentado en producción técnica (embudo y TTV medibles) y guard de onboarding obligatorio antes de rutas principales | Seguimiento operativo (no bloqueante): observar tendencia de completion rate y TTV durante 1–2 ciclos para optimización de UX/copy |
| B3 | EN_CURSO | Cross-liga v1 activo en análisis (`servicios/b3_estabilizacion_futbol.py` + `api/rutas_analisis_futbol.py`), confianza ajustada por muestra, gate semanal por liga en `GET /api/futbol/metricas/b3-estabilidad` y automatización de evidencia con `scripts/reporte_b3_estabilidad.sh` + target `make reporte-b3-estabilidad` (genera `docs/reportes/B3_ESTABILIDAD_*.md`). Se añadió compatibilidad de `scripts/b3_ciclo_semanal.sh` con `X-Usuario-Id` UUID y veredicto explícito para ciclos sin muestra (`docs/reportes/B3_CICLO_SEMANAL_2026-03-26T14-16-17Z.md`). | B3 se gobierna por calidad semanal objetiva (Brier) y evidencia reproducible por ciclo para decisión de cierre | Ejecutar 2 ciclos semanales consecutivos con muestra evaluable y sin ligas en estado crítico; consolidar reporte comparativo de ambos ciclos |
| B4 | EN_CURSO | Backend B4 con preferencias + historial + cola de envío: `GET/PUT /api/notificaciones/preferencias`, `POST /api/notificaciones/encolar-prueba`, `POST /api/notificaciones/scheduler/encolar`, `POST /api/notificaciones/procesar-cola`, `POST /api/notificaciones/enviar-prueba`, `GET /api/notificaciones/historial`, `GET /api/notificaciones/metricas-entrega`; persistencia SQLite con reintentos/backoff y límites por tipo configurables (`NOTIF_MAX_INTENTOS_*`), tick automatizable (`scripts/notificaciones_scheduler_tick.sh`) y plantilla cron (`deploy/staging/cron-notificaciones.example`). Frontend en `PaginaConfiguracion` integra toggles + guardar + prueba + panel de métricas con semáforo; criterio formal de cierre documentado en `docs/reportes/B4_SLO_CICLO_2026-03-18T13-30-08Z.md`. Se ajustó `scripts/b4_ciclo_24h_reporte.sh` para header `X-Usuario-Id` y límite válido de historial (100), con reporte operativo generado (`docs/reportes/B4_CICLO_24H_2026-03-26T14-16-17Z.md`). | B4 tiene flujo E2E operativo, observabilidad de entrega y SLO formal definido | Ejecutar 1 ciclo operativo real (24h) con envíos no nulos y cumplimiento de SLO para cierre formal |
| B5 | EN_PAUSA (chat oculto) | Backend de chat permanece implementado (rutas `POST /api/chat/mensaje`, `GET /api/chat/historial`, `POST /api/chat/reset`) pero se desactiva exposición en producto: ruta `/chat` redirigida y acceso removido del `Encabezado` para que no se vea en UI. La especificación de tiers se actualiza para dejar chat como fase futura. | Decisión de producto: chat no entra en fase actual; se preserva código backend para reactivación posterior sin contaminar UX ni arquitectura de acceso por tiers. | Mantener chat oculto hasta instrucción explícita; cuando se reactive, definir alcance comercial/técnico y límites por tier antes de volver a exponer UI. |
| B6 | EN_CURSO | Preflight de hardening ejecutado con evidencia en `docs/reportes/B6_PREFLIGHT_2026-03-26T14-14-04Z.md`; artefactos operativos presentes y hallazgos de secretos faltantes (`MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`) en `deploy/staging/staging.env`. | Hardening productivo ya está en ejecución con checklist reproducible y criterios mínimos de secretos/operación | Completar secretos faltantes, repetir preflight en verde y continuar con runbook de hardening productivo |
| B7 | PENDIENTE | — | Gate final de salida comercial | E2E primer peso |

## Reglas permanentes de documentación
1. Al cerrar bloque: actualizar este archivo.
2. Registrar entrada breve en `CHANGELOG.md`.
3. Actualizar estado ADR (`PROPUESTO/ACEPTADO/SUPERADO`).
4. Eliminar/archivar documentación obsoleta para evitar contexto viejo.
5. Mantener sincronizado el panel de ejecución inmediata en `docs/roadmap_inmediato/00_INDICE_EJECUCION_INMEDIATA.md`.
