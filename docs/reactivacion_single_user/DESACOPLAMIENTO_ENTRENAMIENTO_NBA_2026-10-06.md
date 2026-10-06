# Bloque B — serving NBA sin entrenamiento implícito

**Estado:** implementación en rama de trabajo; pendiente de CI del código y corte operativo. **Dictamen analítico:** NO CERTIFICADO.

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
- [ ] Verificar CI del commit de código y frontend/Compose.
- [ ] Crear artefacto operativo por entrenamiento explícito y comprobar reload real sin nueva versión en Neon.
- [x] Eliminar escritura de telemetría en `GET /api/prediccion/{id}/explicacion`; `Sunset` conserva lectura de los contadores legados y la emisión registra un log estructurado local.
- [ ] Completar auditoría de llamadas indirectas de todos los GET del sistema; las pruebas actuales cubren salud/estado/equipos, explicación y contratos de bitácora existentes.
- [x] Registrar hora real del inicio/fin del ajuste explícito, separada de fechas de partidos.
- [ ] Demostrar `training_outcomes_available_at` y validación out-of-sample antes de considerar el modelo científicamente reproducible.

**Pruebas locales:** PostgreSQL sintético, Python 3.12: 651 passed, 0 failed, 0 skipped, 2 warnings. Dos intentos anteriores usaron esquemas locales erróneos y no se consideran gates válidos; la ejecución final usó `backend/tests/integracion/suite_global_fixture.sql` en una BD desechable `ap_suite_test_*`. Ninguna prueba backend escribió en Neon. La aplicación local del propietario sigue usando el código previo hasta el corte operativo.

## Siguiente acción

Pasar CI del cambio, generar una versión/artifacto **explícitamente** para no degradar el servicio al sincronizar la ruta canónica, verificar que `--reload` no aumenta `modelo_versiones`, y luego continuar con reconciliación de P&L según el orden del plan.
