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
| B | H6/H7/H9, entorno reproducible y CI | H6/H7 cerrados; H9 aún abierto. Inferencia/calibración fútbol exige UUID; consumidores de app usan raw sin procedencia. Suite backend local con PG efímera sintética: 629 passed, 0 failed, 9 skipped; 16 frontend tests, lint y build verdes. CI `50a372e`: 4/4 jobs. Cotejo Neon read-only: 0 pares calibrados con ID en ambos deportes. | Reparar vista SQL productiva mediante migración ensayada, scripts históricos B16/B17/B20 y nueve skips. El 567/567 histórico fútbol sigue sin calibración demostrada |
| C | NBA, fútbol, walk-forward, confidence, odds, data quality, KPIs y observabilidad | 8 partidos NBA de pretemporada ingresados/verificados en Neon; reglas, scorecard local y catálogo KPI v0 publicados. Dictamen **NO CERTIFICADO** por P&L inconsistente, metadatos temporales incompatibles y fútbol sin frescura | Ver `RECERTIFICACION_ANALITICA_2026-10-06.md`; contrastar outcomes independientemente y completar validación temporal antes de promoción o claims |
| D | Explicabilidad avanzada, gobierno de modelos y evolución | Fuera del bloque inmediato | Solo tras recertificación C |

## Dependencia inmediata

El propietario confirmó uso exclusivamente local y decidió mostrar **todos** los registros deportivos como historial personal. La cuenta de mayor actividad aportó la configuración única; la procedencia original quedó en los backups privados. La migración fue ensayada en restauración aislada y aplicada a Neon tras un segundo backup verificado. Ningún cobro ni ingesta se utilizó como prueba de arranque.

## Forma de cierre por bloque

Registrar objetivo, evidencia previa, archivos, decisiones, tests, resultados, riesgos, pendientes y siguiente paso. Actualizar `ESTADO_PROYECTO.md`/`CHANGELOG.md` y este roadmap sin reescribir los informes de auditoría.
