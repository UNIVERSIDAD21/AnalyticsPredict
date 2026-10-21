# Base y calendario para próximos partidos — 2026-10-21

## Estado al cierre de esta pasada

Se preparó y verificó el horizonte 2026-10-21–2026-11-20, sin confundir calendario,
estadísticas históricas y aptitud del modelo.

| Deporte / alcance | Resultado persistido o servido | Verificación |
|---|---|---|
| NBA | 114 fixtures REG añadidos; 118 del mismo horizonte ya existían. Tres resultados finales ESPN fueron añadidos en una operación previa de esta pasada, por separado. | 114/114 IDs únicos, competición/temporada/equipos/fase correctos y marcadores/cuadros en cero; endpoint a 30 días devuelve 232 fixtures NBA. |
| EuroLeague | 69 fixtures futuros añadidos desde calendario oficial, rondas 7–13; ronda 14 empieza después del horizonte. | 69/69 IDs y equipos cruzados explícitamente, fase/temporada/fechas correctos, marcadores y cuartos en cero. |
| Fútbol | 256 fixtures ya existentes en ocho competiciones verificadas; no hubo altas. Dos fechas se corrigieron en sus mismas filas enlazadas por ID ESPN: Toulouse–Troyes y Athletic Club–Espanyol. | 256/256 únicas y servidas; ambas filas siguen PROGRAMADO y sus métricas permanecen NULL. No se importaron copas sin crosswalk fiable. |

El endpoint de fútbol interpreta el horizonte como días locales completos en
America/Bogota y excluye medianoche posterior; así no omite partidos tardíos del
último día. El selector/API de baloncesto admite hasta 500 fixtures. Las consultas de
prueba devolvieron 256 partidos de fútbol y 301 de baloncesto (232 NBA + 69 EuroLeague)
en 30 días. Esta es una captura puntual: no se creó cron ni actualización continua.

## Gaps históricos y significado de NULL

Censo de fútbol REPEATABLE READ / READ ONLY del 2026-10-21 15:19 UTC, anterior a las
correcciones de calendario y sin cambios estadísticos posteriores: 25.226 filas;
24.618 en estado FINALIZADO; 25 de estas sin ambos goles FT y 24.593 con FT completo.
Entre esas 24.593, **4.603 partidos tienen al menos un NULL en los seis campos de
corners, tiros totales y tiros al arco (26.414 celdas)**. Desglose: corners 4.092 por
lado, tiros totales 4.583 por lado y tiros al arco 4.532 por lado. NULL no implica que
el valor exista en una fuente licenciada ni que el campo aplique a todos los partidos.

No se añadió ningún valor histórico de fútbol en esta pasada. Se mantiene NULL donde
no hay evidencia elegible; no se rellenaron ceros, valores de Google ni datos de otra
vuelta/partido. Bayern–Leipzig (20-12-2024) ya estaba completo en el canon y la ficha
de Google difería del valor guardado, por lo que no se sobrescribió.

Una ficha UEFA de Qarabağ–Shkëndija (12-08-2025, vuelta de clasificación) mostró
estadísticas en el navegador, pero UEFA §6.2 prohíbe la recopilación sistemática para
crear una base de datos y el uso del contenido para desarrollar software/modelos. Se
excluyó como fuente de persistencia. El ID de la vuelta Santa Clara–Varaždin tampoco
corresponde al partido de ida Varaždin–Santa Clara y se descartó.

La documentación oficial de SportsAPI Pro revisada el 2026-10-21 declara derecho de
retención y uso interno para análisis/modelado en cuentas Free, sin redistribución.
Sin embargo, el GET autenticado de calendario exacto usado como validación adicional
devolvió **HTTP 403**; no se reintentó ni se eludió el bloqueo. No se llamó al endpoint
de estadísticas ni se aplicaron campos con esta fuente. Esto corrige la duda
contractual anterior, pero no demuestra cobertura por temporada, exactitud de cada
dato ni independencia del upstream.

La base **no está históricamente completa**: quedan 4.603 partidos con gaps entre esos
seis campos, más NULLs de otros campos (periodos, xG, posesión, disciplina y métricas
no publicadas/no aplicables). No se declara cobertura mundial ni exhaustividad de
copas; los códigos dudosos quedan en cuarentena.

## Preparación de uso y límites

- Los selectores y endpoints pueden trabajar con los fixtures verificados ya cargados
  hasta 2026-11-20. La carga fue puntual y no incorpora automáticamente cambios
  posteriores.
- No se reentrenó, activó ni certificó ningún modelo. El modelo y su estado permanecen
  como antes; fútbol sigue sin modelo ML activo y el dictamen global continúa **NO
  CERTIFICADO**. Cargar fixtures no prueba calibración ni calidad predictiva.
- No se arrancaron servidores, no se desplegó la app, no se añadió cron y no se
  modificaron apuestas. Las únicas mutaciones aparte de calendario fueron las tres
  altas NBA finales identificadas y dos fechas programadas de fútbol.
- QA local: 55 backend tests passed, 8 skipped y una advertencia de deprecación;
  2 pruebas frontend, lint y build aprobados.

## Evidencia externa privada

Carpeta `Carpeta de Entregas de Borlty/PUESTA_EN_MARCHA_BASE_Y_CALENDARIOS_2026-10-21/`.
Capturas/postflights del calendario quedan en
`LLENADO_BASE_Y_PUESTA_EN_MARCHA_2026-10-21/` y sus subcarpetas NBA, EuroLeague y
ESPN_FUTUROS. El expediente privado conserva hashes y no contiene credenciales.
