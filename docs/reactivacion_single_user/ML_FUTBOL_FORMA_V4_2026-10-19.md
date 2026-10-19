# Desarrollo ML fútbol V4 — 2026-10-19

Orden del propietario: mejorar el ML de fútbol con los datos actuales y preparar
su validación. **Desarrollo y congelamiento terminados; activación pendiente de
evidencia futura y calibración. NO CERTIFICADO.** Ninguna escritura en Neon.

## Qué se implementó

- Tres diseños Ridge seleccionables: identidad de clubes/contexto de liga,
  forma reciente y combinación de ambos. Forma: medias de ataque/defensa de los
  últimos 5/20 encuentros, descanso y volumen de antecedentes, por local/visitante.
- Las features de cada encuentro se construyen antes de consumir su resultado;
  todos los encuentros con el mismo instante se procesan como bloque. No se usan
  alineaciones, lesiones, cuotas ni datos cuya disponibilidad no se conoce.
- Estandarización aprendida solo en TRAIN; intercepto no penalizado. Selección
  diseño/alpha en CAL con 500 TRAIN efectivos y 100 CAL mínimos, reserva200 en
  máximo180 días, sin dividir empates y sin evaluar equipos con menos de cinco
  antecedentes. No se redujeron los mínimos de V1/V2/V3.
- Después de seleccionar se hace un **refit explícito** con los históricos
  anteriores al corte. Es un artefacto nuevo: los resultados CAL y del desarrollo
  retrospectivo NO son métricas independientes de este artefacto final.
- Predicciones puntuales no negativas; disparos al arco no superan disparos
  totales. No se convierten MAE/residuales en probabilidades o confianza.
- Artefactos JSON completos, SHA256, coeficientes, transformación, orden/nombres
  de features, estado de forma y antecedentes; recarga sin entrenar. Archivos de
  creación exclusiva fuera del repositorio, sin automatismos ni serving modificado.

## Datos y protocolo declarado antes de medir V4

Lectura PostgreSQL `REPEATABLE READ READ ONLY`, cinco ligas y desde julio2023:
5.607 finales fuente; 5.606 completos para goles/disparos, 5.097 para córners.
Un target ausente de goles/disparos y 510 de córners no se imputan a cero. No se
consultaron endpoints deportivos ni se repitieron ingestas del18/10.

Desarrollo mensual enero–mayo, septiembre y octubre2026 hasta el corte del19/10.
En cada ventana, selección CAL previa y refit anterior al EVAL; features de EVAL
congeladas al inicio del mes, sin consumir sus resultados durante esa ventana.
Los históricos ya habían sido observados en trabajos anteriores: esto es
desarrollo exploratorio, no un test históricamente intacto. Los resultados no
son directamente comparables con el79,13% de V1: cambian protocolo, ventanas y
denominador. V1/V2/V3 y sus decisiones no se alteraron ni se reevaluaron.

Baseline más exigente que una media global: media de cada target en su liga,
solo con datos anteriores al corte. Control adicional: Ridge de identidad, sobre
los mismos pares. IC95 pareados por partido y por bloque díaUTC,1000 réplicas,
semilla42; el segundo no modela toda la dependencia longitudinal por equipo.

El denominador comprende **todos los finales válidos del snapshot** de las cinco
ligas en EVAL, también los sin targets completos o con abstención. La consulta
fuente excluye los registros marcados inválidos y los no finalizados; no es un
censo de todos los estados de la base. No se infla n contando los
cuatro targets como cuatro encuentros. Se mantienen 100 pares mínimos, dos meses
con al menos30, cobertura90%, frescura60 días, mejora con ambos IC95 por debajo
de cero y ningún target nominalmente peor que baseline.

## Resultado retrospectivo del procedimiento, no del refit final

| Familia | Pares / candidatos | Cobertura resuelta | MAE modelo / baseline liga | MAE control identidad | IC95 delta por díaUTC | Dictamen de desarrollo |
|---|---:|---:|---:|---:|---|---|
| Goles1T/2T local/visitante | 1.157/1.193 | 96,98% | 0,66508 / 0,68666 | 0,67386 | [-0,02706; -0,01614] | Supera controles estadísticos exploratorios |
| Disparos total/arco local/visitante | 1.157/1.193 | 96,98% | 2,75608 / 3,00735 | 2,83138 | [-0,31091; -0,19654] | Supera controles estadísticos exploratorios |
| Córners1T/2T local/visitante | 619/1.193 | 51,89% | 1,37540 / 1,41739 | 1,40369 | [-0,05951; -0,02358] | No supera cobertura |

La selección final en CAL elige **identidad/alpha1 para goles**, y
**forma/alpha10 para disparos y córners**. No se fuerza el diseño nuevo cuando
otro obtiene menor error CAL. Los refits usan5.202 filas efectivas de un partido
por fila para goles/disparos y4.698 para córners; CAL selección159/159/158.
No tienen todavía métricas fuera de muestra propias.

## Nueva cohorte verdaderamente futura

Declarada el19/10 antes de exportar y ajustar. Inicio20/10 00:00UTC
(19/10 19:00Bogotá), fin01/12 00:00UTC, intervalo exclusivo por la derecha.
251partidos únicos:88octubre y163noviembre. Los cuatro encuentros del19/10
fuera del periodo no se capturan retroactivamente. Se conserva el orden
declaración ≤ snapshot < fin de ajuste ≤ congelamiento < inicio de eventos.

- Goles:251predicciones,0abstenciones, cobertura potencial100%.
- Disparos:251predicciones,0abstenciones, cobertura potencial100%.
- Córners:223predicciones,28abstenciones por falta de cinco antecedentes completos;
  techo88,84%<90%. Esta cohorte no podrá aprobar córners aunque todos los outcomes
  lleguen. No se incorporan datos inventados para elevar ese techo.

Son725filas partido-familia con cuatro valores cada una, **no725partidos**.
Todas las features futuras permanecen congeladas al corte; no se refrescan en
noviembre ni se incorporan predicciones del modelo como si fueran resultados.
Cambios de horario/equipos/competición se excluyen al evaluar y penalizan cobertura.

El evaluador posterior es de lectura/snapshots; mantiene abstenciones, outcomes
pendientes, targets ausentes, periodo incompleto y hashes. No activa automáticamente,
ni siquiera si pasan controles estadísticos. Las probabilidades siguenN/D.

## Límite de activación y siguiente evidencia necesaria

Los finales futuros hacen falta para medir este **artefacto final**, no para
seguir investigando históricos. No se reutilizará su EVAL para ajustar y luego
llamarlo test independiente. Si se calibra una probabilidad, debe separarse el
conjunto utilizado para ajustar el calibrador de una nueva evaluación posterior,
por versión/mercado, antes de una promoción y adaptación explícita a serving.
El JSONV4 es de laboratorio: no se introduce en el loader Ridgelegacy como si
compartieran contrato. La disponibilidad histórica de datos sigue sin acreditarse;
las capturas actuales sí preceden a los eventos de esta cohorte.

No hay cron, espera activa ni tarea futura programada. El primer estado es0pares,
métricasN/D. Fútbol continúa con0MLactivos. NBA2123/apuestas/predicciones/bitácora/
V1/V2/V3 no se modifican. La aplicación local existente no se reinicia.

## Reproducir y evaluar

Desde `backend/`, con rutas externas nuevas:

```bash
.venv/bin/python scripts/desarrollar_futbol_ml.py declarar --salida /ENTREGA/politica.json --inicio 2026-10-20T00:00:00+00:00 --fin 2026-12-01T00:00:00+00:00
.venv/bin/python scripts/desarrollar_futbol_ml.py exportar --politica /ENTREGA/politica.json --snapshot /ENTREGA/datos.json --fixtures /ENTREGA/fixtures.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/desarrollar_futbol_ml.py desarrollar --politica /ENTREGA/politica.json --snapshot /ENTREGA/datos.json --fixtures /ENTREGA/fixtures.json --salida /ENTREGA/desarrollo.json --cohorte /ENTREGA/cohorte.json
.venv/bin/python scripts/desarrollar_futbol_ml.py evaluar --cohorte /ENTREGA/cohorte.json --snapshot /ENTREGA/observacion_posterior.json --salida /ENTREGA/evaluacion_nueva.json
```

Los tres primeros son un ejemplo de protocolo: **no repetir la cohorte ya
congelada ni ejecutar una declaración cuyo inicio dejó de ser futuro**. Para
evaluar después basta exportar una nueva observación con la misma política y usar
la cohorte congelada, sin volver a entrenar. Un solo hilo para limitar recursos.

## Evidencias e incidencia de metadata

Entrega externa `ML_FUTBOL_FORMA_TEMPORAL_V4_2026-10-19`, acta y manifiesto.
Durante la revisión se detectó que el descriptor reutilizado contaba dos filas
por partido, como el Ridgelegacy, aunque V4 usa una. Se corrigió el descriptor y
se generaron salidas nuevas antes de los eventos. También se nombraron los cuatro
targets y se añadieron contadores/techo de cobertura a la cohorte. Coeficientes,
predicciones y métricas numéricas son idénticos; originales conservados como
superados, no borrados ni sobrescritos.
Las salidas vigentes son `DESARROLLO_V4_CORREGIDO.json` y
`COHORTE_FUTURA_V4_CORREGIDA.json`.

Reanudado tras pausa expresa del propietario: reproducidas exactamente las725
predicciones partido-familia y28abstenciones, sin entrenar durante la recarga.
Un nuevo ajuste offline con **el snapshot original** reproduce todo el desarrollo
salvo su reloj/hash derivado; no se regeneró ni sustituyó la cohorte. La observación
READONLY del19/10 a15:02:39UTC confirma0pares/MAEN/D,0versionesMLfútbol y0activos.
Los24calibradoreslegacy existentes no se tocaron y no son calibradores deV4.
Evidencias: `REPRODUCCION_Y_COMPARACION.json`, `RESUMEN_RESULTADOS_FINAL.json`,
`EVALUACION_INICIAL.json` y `ESTADO_INICIAL_READONLY.json`. Las fuentes finales se
archivan aparte; `fuentes_congelamiento/` conserva la primera versión sin corregir.

Nueve pruebas nuevas cubren fuga temporal/empates, refit explícito, exclusiones,
hashes, recarga sin ajustar, coherencia disparos, calendario y salidas externas.
Suite global con PostgreSQL sintético propio:887aprobadas,0fallos,0skips,
dos deprecaciones heredadas. Publicación y CI del SHA final constan en el acta.
