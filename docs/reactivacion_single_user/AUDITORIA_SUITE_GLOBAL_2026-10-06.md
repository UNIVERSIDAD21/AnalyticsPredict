# Auditoría de suite global segura — 2026-10-06

La suite backend se ejecutó sin conexión productiva (`DATABASE_URL=''`, `TEST_PG_ADMIN_URL=''`) para impedir escrituras accidentales en Neon. Resultado final: **578 passed, 19 failed, 11 skipped, 14 warnings**. No se declara verde. Log local: `/tmp/analyticspredict_suite_post_cambios_20261006.log` (no se versiona).

Los 19 fallos son pruebas que exigen PostgreSQL y no disponían de BD desechable en este host: `tests/api/test_metricas_profesionales_endpoints.py` (7), `tests/integracion/test_pipeline_calidad.py` (1), `tests/test_auditoria_sql_real_pytest.py` (1), `tests/test_endpoint_analizar_registro.py` (4), `tests/test_flujo_calibracion_completo.py` (1), `tests/test_rutas_analisis_respuesta.py` (4) y `tests/test_rutas_bitacora_apuestas_analizadas.py` (1). La integración de migración y Compose sí pasaron con PostgreSQL efímero en CI, pero eso no cubre estos 19 casos. `test_auditoria_sql_real_pytest.py` ejecuta DDL y solo debe reintentarse con URL de prueba explícita; no con Neon.

Se repararon tres pruebas smoke que inspeccionaban `app.routes` antes de generar OpenAPI con FastAPI reciente, una importación de función Poisson retirada y una expectativa legacy sobre el lado OVER por defecto. El caso de GET bitácora comprueba ahora que leer no invoca resolución ni DDL. Se añadieron pruebas puras del scorecard de calidad. Estas correcciones no convierten fallos dependientes de BD en tests aprobados.

**Siguiente gate:** ejecutar los 19 sobre PostgreSQL desechable con esquema/fixtures de cada contrato, aislarlos del entorno productivo y corregir fallos reales que afloren. Mantener la suite global como no verde hasta entonces.

## Actualización de ejecución local — 2026-10-06

El corte anterior de 578/19/11 se conserva como antecedente. La suite actual se ejecutó con `backend/scripts/run_suite_global_testdb.py` sobre PostgreSQL 18.6 local ligado únicamente a socket Unix, una base aleatoria eliminada al finalizar y `backend/tests/integracion/suite_global_fixture.sql` sintético. `TEST_PG_ADMIN_URL` solo admite host local/socket `/tmp` y base administradora `postgres`; el runner reemplaza `DATABASE_URL` para el proceso pytest. **Resultado: 621 passed, 0 failed, 9 skipped, 14 warnings.** Log local `/tmp/ap_suite_global_final.log` (no versionado). También pasaron 16 tests frontend, lint, build/typecheck y `npm audit --omit=dev` (0 vulnerabilidades detectadas).

Clasificación de los 19 fallos anteriores: nueve casos NBA tenían gates SQL no relacionados con sus mocks y ahora los aíslan explícitamente; diez contratos SQL sí se ejecutaron sobre la base sintética (7 métricas, 1 calidad, 1 bitácora, 1 auditoría DDL). La prueba de auditoría solo ejecutó `ALTER`/`CREATE VIEW` dentro de la base efímera. Ninguna prueba de este gate se conectó a Neon, ni hizo ingesta o entrenamiento productivo. El esquema de prueba está en el repositorio y no depende de un volcado remoto.

Los nueve skips restantes **no** son aprobaciones tácitas: cinco casos de `motor_futbol/test_predictor.py` requieren reconciliar el contrato legacy de 24 mercados/corte temporal; dos de `test_registro_predicciones.py` aún apuntan a tablas genéricas `temporadas/equipos/partidos` que el esquema activo separa por deporte; dos de `test_resolucion_predicciones.py` exigen fixtures sintéticas de partido/outcome/odds para ejecutar la resolución integral. Estas deudas deben repararse o retirarse justificadamente, no activarse contra Neon.

**Criterio pendiente:** reproducir 0 fallos en CI con PostgreSQL 16 y Python 3.12, inspeccionar los nueve skips y comprobar que el esquema sintético cubre los contratos relevantes. El job de integración ahora invoca el runner global; todavía no se afirma resultado remoto de ese nuevo job.

## Verificación posterior

CI del HEAD `23a554e` pasó **4/4 jobs**, incluido el runner global con PostgreSQL efímera. En el lote H9 siguiente, la suite local pasó **627/0/9** (14 warnings) tras ampliar el esquema y comprobar consumidores con SQL real; el frontend pasó 16 tests, lint y build. El lote H9 aún necesita su propia ejecución alojada. Los nueve skips mantienen la clasificación anterior y no cuentan como aprobaciones.

CI del lote H9 `d3cfd83` pasó **4/4 jobs**. Un cotejo adicional contra la definición read-only de la vista NBA produjo un test SQL real nuevo y **629/0/9** en PostgreSQL local; ese segundo lote aún requiere CI de su propio HEAD. Ninguna de estas ejecuciones recertifica datos o modelos.
