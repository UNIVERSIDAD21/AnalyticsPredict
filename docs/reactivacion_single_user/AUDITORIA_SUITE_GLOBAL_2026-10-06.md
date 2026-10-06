# Auditoría de suite global segura — 2026-10-06

La suite backend se ejecutó sin conexión productiva (`DATABASE_URL=''`, `TEST_PG_ADMIN_URL=''`) para impedir escrituras accidentales en Neon. Resultado final: **578 passed, 19 failed, 11 skipped, 14 warnings**. No se declara verde. Log local: `/tmp/analyticspredict_suite_post_cambios_20261006.log` (no se versiona).

Los 19 fallos son pruebas que exigen PostgreSQL y no disponían de BD desechable en este host: `tests/api/test_metricas_profesionales_endpoints.py` (7), `tests/integracion/test_pipeline_calidad.py` (1), `tests/test_auditoria_sql_real_pytest.py` (1), `tests/test_endpoint_analizar_registro.py` (4), `tests/test_flujo_calibracion_completo.py` (1), `tests/test_rutas_analisis_respuesta.py` (4) y `tests/test_rutas_bitacora_apuestas_analizadas.py` (1). La integración de migración y Compose sí pasaron con PostgreSQL efímero en CI, pero eso no cubre estos 19 casos. `test_auditoria_sql_real_pytest.py` ejecuta DDL y solo debe reintentarse con URL de prueba explícita; no con Neon.

Se repararon tres pruebas smoke que inspeccionaban `app.routes` antes de generar OpenAPI con FastAPI reciente, una importación de función Poisson retirada y una expectativa legacy sobre el lado OVER por defecto. El caso de GET bitácora comprueba ahora que leer no invoca resolución ni DDL. Se añadieron pruebas puras del scorecard de calidad. Estas correcciones no convierten fallos dependientes de BD en tests aprobados.

**Siguiente gate:** ejecutar los 19 sobre PostgreSQL desechable con esquema/fixtures de cada contrato, aislarlos del entorno productivo y corregir fallos reales que afloren. Mantener la suite global como no verde hasta entonces.
