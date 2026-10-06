# Bloque B — serving NBA sin entrenamiento implícito

**Estado operativo:** integrado en `reactivacion/implementacion-single-user` (`8a7465c`), CI 4/4 y reload real sin autoentrenamiento. **Dictamen analítico:** NO CERTIFICADO.

## Diagnóstico

`app.ciclo_de_vida` llamaba `GestorModelo.inicializar_async()`; ese método ejecutaba `EntrenadorBD.entrenar()` y registraba una versión en `modelo_versiones`. También iniciaba una tarea periódica que podía entrenar al detectar partidos nuevos. Por tanto cada startup/reload podía añadir una versión y la ingesta podía disparar entrenamiento sin orden explícita. La API no tenía un artefacto versionado cargable que preservara serving al reiniciar.

## Contrato nuevo

- Startup/reload: solo carga `~/.local/share/analyticspredict/modelo_nba_activo.npz` (o `ANALYTICSPREDICT_MODELO_NBA_ACTIVO`), sin abrir BD para el modelo ni crear versiones. Si falta o es inválido, la API inicia y `/salud` informa modo degradado; análisis NBA espera un artefacto válido.
- Entrenamiento: solo `python scripts/entrenar_modelo_nba_explicito.py --entrenar` desde `backend`, o `POST /api/modelo/reentrenar`, registra versión en PostgreSQL y publica el artefacto fuera del repositorio. El comando sin `--entrenar` no escribe.
- Tras usar el CLI con la API ya abierta: `POST /api/modelo/cargar` lee el artefacto y actualiza memoria **sin** entrenar ni registrar otra versión.
- El artefacto guarda `modelo_version_id`, versión registrada, hash de dataset, feature set, fechas extremas observadas, alpha, métricas de entrenamiento y timestamps reales del inicio/fin del **ajuste**. **`training_outcomes_available_at` y métricas de validación son `null`**: la fecha histórica del partido no demuestra disponibilidad de outcomes ni validación temporal. No confundir fin de cómputo con cutoff científico; no afirmar certificación completa con esos campos ausentes.
- Ingesta y listener legacy no entrenan automáticamente; el operador decide cuándo entrenar. GET de salud/estado/equipos del modelo no entrena ni abre BD en pruebas aisladas.

## Checklist y aceptación

- [x] Identificar llamadas de entrenamiento en startup y tarea periódica.
- [x] Separar carga de artefacto de entrenamiento.
- [x] Preservar ID real de versión y fecha del entrenamiento en el artefacto.
- [x] Publicar archivo atómicamente y cargarlo sin pickle.
- [x] Mantener healthcheck operativo sin artefacto/BD de entrenamiento.
- [x] Probar dos ciclos de startup/reload sin entrenamiento ni conexión de modelo a BD.
- [x] Probar que solo una invocación explícita entrena y que el CLI exige `--entrenar`.
- [x] Probar recarga de versión publicada sin otra versión.
- [x] Verificar CI del commit de código y frontend/Compose: PR run `37534587737` y rama run `37534829259`, ambos 4/4.
- [x] Crear artefacto operativo por entrenamiento explícito y comprobar reload real sin nueva versión en Neon: modelo ID 2122, versión 2111; tabla pasó 2.121→2.122 por CLI y permaneció en 2.122 tras reload.
- [x] Eliminar escritura de telemetría en `GET /api/prediccion/{id}/explicacion`; `Sunset` conserva lectura de los contadores legados y la emisión registra un log estructurado local.
- [x] Eliminar el incremento de telemetría a archivo invocado por cada GET de bitácora; el endpoint de consulta de uso conserva lectura histórica. Rutas activas auditadas por DML/archivo en GET y helpers locales; no se encontraron otras escrituras persistentes alcanzables.
- [ ] Extender la auditoría a dependencias externas/dinámicas antes de afirmar ausencia absoluta de cualquier side effect; observabilidad en memoria sí registra latencia HTTP.
- [x] Registrar hora real del inicio/fin del ajuste explícito, separada de fechas de partidos.
- [ ] Demostrar `training_outcomes_available_at` y validación out-of-sample antes de considerar el modelo científicamente reproducible.

**Pruebas locales:** PostgreSQL sintético, Python 3.12: 651 passed, 0 failed, 0 skipped, 2 warnings. Dos intentos anteriores usaron esquemas locales erróneos y no se consideran gates válidos; la ejecución final usó `backend/tests/integracion/suite_global_fixture.sql` en una BD desechable `ap_suite_test_*`. Ninguna prueba backend escribió en Neon. Servidor canónico del Jefe: `/salud` 200 saludable, `/api/modelo/estado` 200 con ID 2122 y 58 equipos. El proceso del Jefe no se detuvo. Evidencia externa `OPERACION_MODELO_NBA_EXPLICITO_2026-10-06`.

## Siguiente acción

Continuar reconciliación de P&L, temporalidad y procedencia de outcomes según el orden del plan. Mantener N/D en validación temporal/out-of-sample: el último partido usado por este entrenador es del 2026-05-05.
