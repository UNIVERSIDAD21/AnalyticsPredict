# Roadmap de reactivación AnalyticsPredict

**Directiva vigente:** plan single-user del propietario del 2026-10-05. Esta secuencia sustituye C0–C7 comerciales. `CERRADO` solo se usa con evidencia; diseño documental no equivale a implementación.

| Bloque | Objetivo | Estado al 2026-10-05 | Gate para avanzar |
|---|---|---|---|
| A0 | Snapshot, mapa de impacto, arquitectura, endpoints y migración | Documentado; rama de recuperación creada | Verificar mapa contra código al ejecutar cambios |
| A1 | Perímetro privado en todos los entornos y datos | Cerrado para uso local confirmado por el propietario; servicios ligados a loopback | Revalidar si cambia la topología |
| A2 | Retirar auth/login y headers/tokens | Cerrado para código/API/UI activos; OpenAPI sin identidad | Vigilar regresiones |
| A3 | Retirar pagos, suscripciones y tiers | Cerrado para código/API/UI/BD activos | Vigilar regresiones |
| A4 | Migrar configuración, bitácora y datos históricos | Cerrado: backup verificado, ensayo y Neon migrada; 182/13/7/16 conservados | Backups privados recuperables |
| A5 | Limpiar legacy/config/DB versionadas y reportar eliminación | Parcial: DB/telemetría desversionadas, esquemas sin consumidores retirados, Compose privado probado en runner; inventario legacy y preflight H4 publicados | Revisar scripts sin uso y 168 refs/2 PR antes de intentar purga histórica; Docker local no requerido para CI |
| B | H6/H7/H9, entorno reproducible y CI | H6/H7 cerrados; H9 técnico de vistas resuelto en Neon, H9 científico aún abierto. Suite backend local Python 3.12/PG sintético: 657 passed, 0 failed, 0 skipped; 16 frontend tests, lint y build verdes. B16/B17/B20 y calibración temporal corregidos. Ambas vistas NBA migradas transaccionalmente tras ensayo/rollback; contrato 42/12, permisos y 2.934 filas preservados. CI de PR #167 y rama canónica: 4/4 verde. Serving NBA separado del entrenamiento; reload conserva versión 2122 sin nueva escritura. | Obtener pares temporalmente elegibles/outcomes prospectivos y recertificar. `GOLES_FT` tiene 0 elegibles en diagnóstico read-only; histórico fútbol 567/567 sigue sin calibración demostrada |
| C | NBA, fútbol, walk-forward, confidence, odds, data quality, KPIs y observabilidad | 8 partidos NBA de pretemporada ingresados/verificados en Neon; reglas, scorecard local y catálogo KPI v0 publicados. P&L de 181 binarios clasificado read-only: 103 no evaluables para ROI, 78 conciliables solo aritméticamente; API/UI muestran N/D en cortes afectados. Dictamen **NO CERTIFICADO** por P&L inconsistente, metadatos temporales incompatibles y fútbol sin frescura | Ver `RECERTIFICACION_ANALITICA_2026-10-06.md`; contrastar outcomes independientemente y completar validación temporal antes de promoción o claims |
| D | Explicabilidad avanzada, gobierno de modelos y evolución | Fuera del bloque inmediato | Solo tras recertificación C |

**Corte de calidad por competición (2026-10-06):** el total 12.775 usado en algunos informes era baloncesto agregado. NBA tiene 10.286 partidos y 148 marcadores 0–0; Euroliga, 2.489 y 83. La consulta ESPN de los 148 NBA encontró 67 pospuestos y 81 finales no reflejados en los totales locales. Se corrigió el auditor/scorecard NBA; no se repararon filas históricas ni se certificó rendimiento. Bloque C/E sigue abierto por reconciliación, Euroliga y validación prospectiva.

## Dependencia inmediata

El propietario confirmó uso exclusivamente local y decidió mostrar **todos** los registros deportivos como historial personal. La cuenta de mayor actividad aportó la configuración única; la procedencia original quedó en los backups privados. La migración fue ensayada en restauración aislada y aplicada a Neon tras un segundo backup verificado. Ningún cobro ni ingesta se utilizó como prueba de arranque.

## Forma de cierre por bloque

Registrar objetivo, evidencia previa, archivos, decisiones, tests, resultados, riesgos, pendientes y siguiente paso. Actualizar `ESTADO_PROYECTO.md`/`CHANGELOG.md` y este roadmap sin reescribir los informes de auditoría.
