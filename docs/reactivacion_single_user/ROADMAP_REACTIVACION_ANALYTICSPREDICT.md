# Roadmap de reactivación AnalyticsPredict

**Directiva vigente:** plan single-user del propietario del 2026-10-05. Esta secuencia sustituye C0–C7 comerciales. `CERRADO` solo se usa con evidencia; diseño documental no equivale a implementación.

| Bloque | Objetivo | Estado al 2026-10-05 | Gate para avanzar |
|---|---|---|---|
| A0 | Snapshot, mapa de impacto, arquitectura, endpoints y migración | Documentado; rama de recuperación creada | Verificar mapa contra código al ejecutar cambios |
| A1 | Perímetro privado en todos los entornos y datos | Cerrado para uso local confirmado por el propietario; servicios ligados a loopback | Revalidar si cambia la topología |
| A2 | Retirar auth/login y headers/tokens | Cerrado para código/API/UI activos; OpenAPI sin identidad | Vigilar regresiones |
| A3 | Retirar pagos, suscripciones y tiers | Cerrado para código/API/UI/BD activos | Vigilar regresiones |
| A4 | Migrar configuración, bitácora y datos históricos | Cerrado: backup verificado, ensayo y Neon migrada; 182/13/7/16 conservados | Backups privados recuperables |
| A5 | Limpiar legacy/config/DB versionadas y reportar eliminación | Parcial: DB/telemetría desversionadas, scripts comerciales retirados, Compose local desacoplado de auth/SMTP y probado en runner con puertos loopback | Inventario final legacy y revisión histórica de blobs; Docker local no requerido para CI |
| B | H6/H7/H9, entorno reproducible y CI | H6/H7 y calibración fútbol H9 corregidos; Python 3.12 fijado, migración PostgreSQL efímera y Compose pasaron CI. Smoke visual de rutas clave con datos no vacíos; ROI histórico rotulado no certificado | Auditar H9 en otros consumidores y suite global segura; revisar auto-resolución en GET que intentó escribir durante smoke read-only |
| C | NBA, fútbol, walk-forward, confidence, odds, data quality, KPIs y observabilidad | Corte de solo lectura 2026-10-06 ejecutado; **NO CERTIFICADO** por datos sin frescura, P&L inconsistente y metadatos temporales incompatibles | Ver `RECERTIFICACION_ANALITICA_2026-10-06.md`; corregir evidencia antes de promoción o claims |
| D | Explicabilidad avanzada, gobierno de modelos y evolución | Fuera del bloque inmediato | Solo tras recertificación C |

## Dependencia inmediata

El propietario confirmó uso exclusivamente local y decidió mostrar **todos** los registros deportivos como historial personal. La cuenta de mayor actividad aportó la configuración única; la procedencia original quedó en los backups privados. La migración fue ensayada en restauración aislada y aplicada a Neon tras un segundo backup verificado. Ningún cobro ni ingesta se utilizó como prueba de arranque.

## Forma de cierre por bloque

Registrar objetivo, evidencia previa, archivos, decisiones, tests, resultados, riesgos, pendientes y siguiente paso. Actualizar `ESTADO_PROYECTO.md`/`CHANGELOG.md` y este roadmap sin reescribir los informes de auditoría.
