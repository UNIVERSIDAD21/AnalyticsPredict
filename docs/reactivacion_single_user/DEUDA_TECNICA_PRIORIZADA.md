# Deuda técnica priorizada — reactivación single-user

**Corte:** 2026-10-05. Prioridades derivadas del plan del propietario y H1–H12 de la auditoría histórica; no equivalen a certificación actual.

> **Adenda 2026-10-06:** la vista H9 ya fue migrada en Neon y su semántica técnica está cerrada; el H9 científico sigue abierto. H4 no está purgado: cuatro blobs SQLite comerciales siguen alcanzables en la historia/ref visibles. H7/side-effects GET y suite deben juzgarse con la evidencia posterior, no con el estado de los primeros smoke tests. El P&L vigente excluye 114/181 binarias (115/182 totales) y continúa NO CERTIFICADO. H12, independencia de outcomes, fútbol, temporalidad y prospectiva permanecen abiertos.

> **Mantenimiento posterior:** H12 retiró tres JSON vacíos del índice Git sin fabricar datos, quitó un target B4 roto y fijó CI a Ubuntu 24.04 con acciones v6; H12 solo podrá cerrarse tras CI de este cambio y revisión restante de permisos/project rot. H4 tiene mirror/bundle fresco: 12 heads y 13 refs `pull/167`–`pull/179` aún alcanzan los cuatro blobs; reescribir únicamente ramas sería una purga incompleta. Las PR #150 y #23 se cerraron por política 403 y obsolescencia, respectivamente.

| Prioridad | Trabajo | Criterio verificable | Estado |
|---|---|---|---|
| P0 | Perímetro privado antes de retirar auth | Backend sensible ligado a loopback | Cerrado para uso exclusivamente local confirmado; revalidar ante otra topología |
| P0 | Inventario y migración de `usuario_id`/FK | Ensayo aislado y conteos idénticos | Cerrado: backup privado verificado, todos los registros deportivos conservados |
| P0 | Retirar login/auth, pagos, MP, suscripciones y tiers sin perder análisis | OpenAPI/UI sin superficies comerciales, headers/tokens ni gates; NBA/fútbol/bitácora íntegros | Cerrado en código/API/UI/BD activos; smoke visual y HTTP |
| P1 | H6 escala `hit_rate_sin_push` | Casos 0/50/56/100%, backend/FE coherentes | Corregido; tests numéricos y build |
| P1 | H7 envelopes y estados de bitácora | Lista y tarjetas no vacías, error no convertido a cero | Clientes v2 y pruebas FE/BE dirigidas; smoke visual con datos no vacíos. GET de bitácora intentó auto-resolución/escritura bajo conexión read-only: revisar side effect. |
| P1 | H9 métricas Brier/ECE/LogLoss | Medición real o `null` explícito, tests numéricos | Código y suite sintética avanzados: 646 passed/0 skipped, B16/B17/B20 con procedencia, calibración temporal sin sintéticos. Sigue abierto: vista NBA productiva no migrada, pares prospectivos/frescura y verificación de UI por mercado. |
| P1 | H11 entorno reproducible y H10 CI | BD efímera, unit/contract/integration/FE/build en CI | Lock Python 3.12, integración PG y smoke Compose alojado en verde (run 37481234870); suite global y Docker local no certificados. |
| P1 | H4 SQLite versionadas | Retirar seguimiento sin borrar evidencia; clasificar credenciales | DB comerciales retiradas del índice Git e ignoradas; copias locales preservadas. Historial Git anterior aún contiene blobs. |
| P1 analítico | H8 walk-forward real/no-leakage | `fit_end < prediction_time < outcome_time`, snapshots/model IDs | Bloqueado: 2.136/2.934 NBA enlazan a cutoff posterior al día de generación; no hay prueba de no-leakage. |
| P2 analítico | Recertificar NBA/fútbol, confidence, odds, calidad y KPIs | Cortes actuales, n/método/limitaciones, sin rentabilidad futura | Corte read-only 2026-10-06 ejecutado; luego 8 partidos NBA de pretemporada ingresados y verificados. **NO CERTIFICADO**: 102/181 P&L NBA inconsistentes, fútbol sin frescura y 3–4 pares/mercado; ver reporte. |
| P3 | H12 permisos/reportes vacíos y project rot | Reparación específica con evidencia, no limpieza estética | Pendiente; 30 cambios de modo preexistentes preservados |

H1–H3 no se cierran por decisión de producto sino al probar la desaparición de sus superficies. Fútbol permanece beta hasta evidencia cuantitativa actual; el análisis NBA interno mantiene política sin picks/stakes/recomendaciones.
