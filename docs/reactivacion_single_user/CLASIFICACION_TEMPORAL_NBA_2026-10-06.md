# Clasificación temporal histórica NBA — no confundir fecha con evidencia

**Corte:** 2026-10-06, Neon bajo transacción READ ONLY. **Dictamen:** ninguna predicción histórica cumple el gate de temporalidad certificable; no hay walk-forward prospectivo demostrado.

## Semántica observada

| Campo | Significado que puede probarse | Límite |
|---|---|---|
| `modelo_versiones.fecha_entrenamiento` | Timestamp de registro de versión en BD | No es `fit_end` del ajuste ni hora de disponibilidad del último outcome |
| `modelo_versiones.cutoff_entrenamiento` | Fecha declarada del corte de entrenamiento | Sin hora ni prueba de que todos los outcomes/features ya estaban disponibles |
| `predicciones_registradas.timestamp_generacion` | Timestamp de inserción/generación de predicción (`timestamptz`) | No prueba que la predicción se congeló antes del inicio del evento |
| `predicciones_registradas.fecha_partido` | Fecha calendario (`date`) | No hay hora de inicio ni zona canónica demostrada para todo el histórico |
| `predicciones_registradas.timestamp_resolucion` | Hora de registro de la resolución | No es por sí sola `outcome_time` independiente del proveedor |
| Features y cuotas | No hay timestamps propios por predicción | No reconstruir conocimiento disponible con fechas de carga actuales |

La comparación de instantes usa **UTC**. El ingestor NBA nuevo deriva `fecha_partido` de `event.date` ISO, pero el scraper histórico extrae el calendario sin convertir zona; por ello un `timestamp_generacion` en UTC con fecha **un día posterior** a `fecha_partido` no demuestra por sí solo que la predicción fue posterior al inicio del juego. No se inventa hora de salto inicial ni se cambia la fecha para arreglar casos.

## Resultado por fila

| Clase | n / 2.934 | Motivo principal |
|---|---:|---|
| `TEMPORALMENTE_INVALIDA` **para certificación** | 2.136 | Cutoff de entrenamiento fechado después del día UTC de generación. Incompatibilidad de metadatos; no demuestra por sí sola que el modelo efectivamente usó información futura. |
| `AMBIGUA` | 476 | 42 cutoff y generación el mismo día; 434 con cutoff previo pero solo fecha de partido sin hora/semántica suficiente. |
| `NO_DETERMINABLE` | 322 | Resultado/resolución posterior aún no registrada, además de horas independientes ausentes. |
| `TEMPORALMENTE_VALIDA` | **0** | No existe cadena probada `fit_end < prediction_time < game_start < outcome_time`. |

Los grupos son excluyentes. La auditoría anterior contaba 756 cutoffs anteriores: ahora **434 ambiguas + 322 no determinables**, sin promover ninguna a válida. En los 2.934 casos hay versión referenciada; `fecha_entrenamiento` no es posterior a la generación. Cuarenta y dos cutoffs del mismo día siguen ambiguos. `timestamp_resolucion` falta en 322. El archivo privado de la entrega `TEMPORALIDAD_HISTORICA_NBA_2026-10-06` guarda estado/motivo por ID; no se alteró predicción alguna.

## Búsqueda de reconstrucción

- Las 2.934 predicciones referencian **1.467 IDs de modelo**. Esas versiones tienen `hash_datos`, `cutoff_entrenamiento`, `fecha_min_entrenamiento`, pero `metadata` histórica solo aporta `fecha_max_entrenamiento` y `config_entrenamiento` aporta `alpha`; no trae hora de `fit_end` ni disponibilidad de resultados.
- En el checkout existe `backend/scripts/datos/modelo_entrenado.npz` histórico (último commit de ese archivo de enero), no 1.467 artefactos inmutables vinculados a los IDs. El artefacto operativo nuevo del ID 2122 no reconstruye los anteriores.
- De los partidos enlazados, 2.560 tienen `source=ESPN` y 374 no tienen fuente. No se encontraron timestamps de features, cuotas o kickoff en las tablas consultadas.
- La hora de resolución en BD no sustituye una fuente independiente de resultado. Un commit o log de despliegue tampoco demuestra por sí solo qué datos tenía cada modelo.

## Política de uso

Excluir **2.934/2.934** de cualquier afirmación histórica de walk-forward «sin leakage» o ROI/accuracy prospectivo certificado. Métricas descriptivas raw pueden mostrarse con `n` y advertencia, nunca como validación temporal. Reclasificar solo si aparecen snapshots, artefacto/versión, hora de features, kickoff, odds y outcome comprobables. Para la cadena nueva, congelar esos campos antes de cada partido y esperar outcomes posteriores.

**Reproducción:** `backend/scripts/auditar_temporalidad_nba.py` (solo SELECT, `SET TRANSACTION READ ONLY`) con JSON por fila fuera del repositorio. Pruebas unitarias cubren cutoff futuro, mismo día, ausencia de outcome/zona y la condición estricta de validez.

## Checklist y criterio de aceptación

- [x] Clasificación excluyente de las 2.934 filas con ID y motivo reproducible.
- [x] Conservación del histórico y consulta productiva en modo solo lectura.
- [x] Exclusión de las 2.934 filas de afirmaciones de walk-forward libre de leakage.
- [x] Suite backend sobre PostgreSQL desechable: 661 passed, 0 failed, 0 skipped.
- [ ] Subconjunto con instantes independientes `fit_end < prediction_time < game_start < outcome_time`: **0**; pendiente nueva evidencia, no se puede certificar el histórico.
- [ ] Reconstrucción de disponibilidad de features/cuotas históricas: faltan snapshots y timestamps.

**Siguiente acción:** abrir cadena prospectiva con artefacto/versionado, snapshot y hora de evento/outcome independientes; solo después evaluar temporalidad y métricas por ventana. El criterio de aceptación científica permanece **NO CUMPLIDO**.
