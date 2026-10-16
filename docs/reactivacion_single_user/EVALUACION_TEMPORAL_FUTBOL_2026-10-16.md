# Evaluación temporal Ridge fútbol — 2026-10-16

## Resultado y alcance

**Evaluación retrospectiva ejecutada; ninguna familia apta para activación con
los gates predeclarados. NO CERTIFICADO.** No se guardaron modelos, activaciones,
predicciones, calibradores ni cambios de esquema en Neon. Los ajustes Ridge se
hicieron en memoria después de una lectura en transacción `READ ONLY`.

El snapshot se observó el **2026-10-16T03:15:44.040953Z** (15 de octubre en Bogotá).
La publicación posterior no cambia esa fecha ni lo convierte en evidencia prospectiva.

## Protocolo fijado antes de medir

- Cinco ligas: ENG_PREMIER, ESP_LALIGA, ITA_SERIEA, GER_BUNDESLIGA y FRA_LIGUE1.
- TRAIN desde 2023-07-01 hasta el inicio de CAL; CAL de aproximadamente tres meses;
  EVAL en enero, febrero, marzo, septiembre y octubre de 2026 (hasta el día 16 exclusivo).
- Particiones por fecha UTC y partido completo. Solo TRAIN genera dos perspectivas;
  CAL/EVAL cuentan cada partido una vez. Mapa de equipos y mínimo de cinco partidos
  por equipo calculados solo en TRAIN; equipos desconocidos se excluyen y cuentan.
- Alpha 1/5/10 seleccionado solo con MAE en CAL. Sin reajustar con CAL ni elegir
  hiperparámetros con EVAL. CAL **no** es un calibrador probabilístico.
- Mínimos por ventana: 500 TRAIN, 100 CAL y 30 EVAL. La ausencia de CAL no se suple
  con error de entrenamiento. Los splits de CV tampoco separan empates temporales
  ni devuelven ajuste in-sample como si fuera validación cuando faltan folds.
- Baseline: media de cada target en TRAIN, perspectiva local, sobre la misma
  cohorte EVAL. MAE/RMSE promedian los cuatro targets por familia.
- Bootstrap pareado, 1.000 réplicas, semilla 42, unidad **partido**. No modela toda
  la dependencia temporal/equipo entre partidos; no es un intervalo prospectivo.
- Gate exploratorio: al menos 100 partidos y dos ventanas evaluadas, cobertura
  global >=90%, último target <=60 días, límite superior del IC95 de delta MAE <0
  y ningún target nominalmente peor que baseline. No equivale a promoción beta.

Hash SHA-256 de la política predeclarada:
`cf466ed77a57181a9596956fbcb2085c074d07315ee4a7704ee25a63a2afa11a`.
Snapshot de datos deportivos:
`52afec11744b7b45fc9f55366d1a8babcea8b1538f4ec6a5edb7a9fd060c4010`.
La disponibilidad histórica de esos datos en cada fecha **no está acreditada**.

## Resultados agregados

| Familia | Dataset efectivo acotado | Partidos EVAL | MAE Ridge / baseline | RMSE Ridge / baseline | IC95 delta MAE | Cobertura EVAL |
|---|---:|---:|---:|---:|---|---:|
| Corners 1T/2T local/visitante | 4.897 | 581 | 1,396 / 1,426 | 1,772 / 1,797 | [-0,0515; -0,0091] | 100% de candidatos con targets |
| Goles 1T/2T local/visitante | 4.897 | 581 | 0,665 / 0,686 | 0,817 / 0,830 | [-0,0306; -0,0126] | 100% de candidatos con targets |
| Disparos total/arco local/visitante | 5.097 | 618 | 2,679 / 2,907 | 3,615 / 3,955 | [-0,3050; -0,1537] | 79,13% |

Estos datasets están acotados a cinco ligas y desde julio de 2023: no sustituyen
los conteos globales de diagnóstico del bloque de persistencia. Los 201 partidos
sin targets completos de corners/goles no entran en su denominador de cobertura:
el 100% **no significa** cobertura de partidos recientes ni de todos los finales.

| Ventana | TRAIN | CAL efectivo/candidato | EVAL corners y goles | EVAL disparos efectivo/candidato | Resultado |
|---|---:|---:|---:|---:|---|
| Enero | 3.786 | 522/522 | 222 | 222/222 | Evaluadas las tres familias |
| Febrero | 3.951 | 579/579 | 193 | 193/193 | Evaluadas las tres familias |
| Marzo | 4.139 | 584/584 | 166 | 166/166 | Evaluadas las tres familias |
| Septiembre | 4.889 | 0/0 | 0 | 121/153 conocidos, no evaluados | CAL insuficiente |
| Octubre | 4.889 | 0/0 corners/goles; 121/153 disparos | 0 | 37/47 | Solo disparos evaluado |

Los 153 candidatos de septiembre sin CAL sí penalizan la cobertura agregada de
disparos. En octubre se cuentan diez partidos con equipo desconocido, no se usan
vectores vacíos ni se borran del denominador para aprobar el gate.

## Decisión por familia

- **Corners:** sin frescura y un target peor nominalmente que baseline; no activar.
- **Goles:** sin frescura de targets por tiempos; no activar.
- **Disparos:** cobertura agregada insuficiente; no activar.

No se cambiaron ventanas ni umbrales tras observar el resultado. Esto no impide
investigar nuevos datos ni un futuro protocolo distinto, declarado antes de medir;
tampoco obliga a publicar un modelo que no cumple el protocolo actual.

## Reproducción y evidencias

CLI de lectura explícita: `backend/scripts/evaluar_futbol_temporal.py`, con
`--politica`, `--snapshot` y `--salida` externos. Un intento de DML a través de su
pool se rechaza en PostgreSQL. Pruebas de no mezcla entre partidos, cambios de
outcome EVAL que no alteran alpha/coeficientes, mínimos, equipos desconocidos,
IDs duplicados, bootstrap y fechas/políticas inválidas.

Primera suite global del WIP: **784 passed, cero fallos y cero skips**, dos
deprecaciones heredadas. La comprobación de publicación se registra en el acta.
Artefactos deportivos y logs fuera del repositorio:
`EVALUACION_TEMPORAL_Y_CONTINUIDAD_2026-10-16` en la Carpeta de Entregas de Borlty;
incluye política, snapshot, reporte por partido, resumen y SHA256SUMS. Conserva
los originales de `PLAN_MAESTRO_EJECUCION_BORLTY_2026-10-15`.

Siguiente: KPI/caches y auditoría GET; fuentes por tiempos/cobertura tienen su
propio trabajo. No repetir capturas NBA ni entrenamientos/ingestas ya cerrados.
