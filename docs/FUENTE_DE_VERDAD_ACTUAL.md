# FUENTE_DE_VERDAD_ACTUAL — AnalyticsPredict

## Agenda global y consulta retrospectiva de fútbol — 2026-10-26

`/futbol` permite navegar por día entre todas las competiciones y seleccionar
un encuentro sin mezclar la fecha de agenda con las temporadas del cálculo.
Los encuentros iniciados se reconstruyen con corte exclusivo en el kickoff,
incluso si su estado sigue pendiente: transacción de solo lectura, sin ML actual,
registro de pronósticos ni apuestas. No se cambian estados para habilitar consultas.
Actualizar agenda solo relee la BD; no descarga calendarios ni marcadores.

Publicación acotada a agenda y prerrequisitos de fútbol (elegibilidad, contexto,
catálogo y contratos compartidos); otros trabajos locales conservan su alcance.
Validación del candidato aislado: 1.369 backend/0 omitidas y 125 frontend,
lint/TypeScript/build y auditoría de producción aprobados. Estos son controles
locales: la CI remota se verifica por SHA en el acta externa de publicación.
[Contrato de agenda](reactivacion_single_user/AGENDA_FUTBOL_2026-10-26.md).

Este archivo es el punto de entrada oficial para trabajo operativo y técnico.

## Muestra WNBA por mercado — 2026-10-25

Q1–Q4 PRE no requieren muestra OT. Si faltan diez casos OT, solo el total con
prórroga y sus derivados quedan N/D; se conservan cuartos y regulación separada.
Regresión solo2020 y ocho temporadas aisladas verificadas; sin modificar artefactos
ni journals. [Contrato y matriz de temporadas](reactivacion_single_user/MUESTRAS_WNBA_POR_MERCADO_2026-10-25.md).

## Paridad WNBA con el recorrido NBA — 2026-10-25

Configuración/resultados NBA compartidos, sin resultado WNBA alternativo.
PRE completo con OT empírico WNBA; cierres Q1–Q3 de regulación mediante
covarianza condicional propia, sin reloj/posesiones ni parámetros NBA.
Score/stake/confianza sin política acreditada conservan campos con N/D; RAW.
Calendario móvil de tres meses: 25oct–25ene, tres fixtures oficiales publicados
(26/29/31oct, último condicional); publicación íntegra oficial2027 no acreditada.
Identidades/revisiones sin puntos ficticios; enlace posterior a FT canónico,
guardado explícito con revisión vigente y combinadas WNBA conjuntas propias.
V1/cohortes originales conservados; v2 evaluado por separado:450/616 por modo,
166 abstenciones; no superioridad general/calibración/prospectiva.
[Contrato, matriz, calendario y operación](reactivacion_single_user/PARIDAD_WNBA_2026-10-25.md).

## WNBA integrada y usable — 2026-10-25

Baloncesto permite `?liga=wnba`, equipos y temporadas anuales efectivas, corte
conservador y predictor Ridge **WNBA propio**, Q1–Q4/total40min sin OT ni live.
1.997 REG/POST elegibles (1.840 REG), 15 equipos de liga, snapshot2019–2026.
Publicación `wnba-v1-912782c821ae18d8895a723a`. Candidato temporal450/616 EVAL,166 abstenciones;
MAEtotal15,2951 vs15,3209 referencia: sin superioridad general ni calibración
acreditada. Refit/alcances personalizados no heredan métricas de ese candidato.
Journal y versiones aislados; manual/histórico/prueba no son apuestas oficiales.
Sin nuevas migraciones/DML, entrenamiento o cambios de modelos ajenos.
[Uso, contrato, evaluación y actualización](reactivacion_single_user/PREDICTOR_WNBA_2026-10-25.md).

## Ingesta local WNBA — 2026-10-25

Importador de archivos suministrados por el propietario, sin nuevas consultas ESPN.
Identidades WNBA propias, temporadas anuales, finales en resultados compartidos y
no finalizados persistidos en tabla fuente con NULL y sin resultado ficticio.
Conserva estadísticas/OT detallado/evidencias y cuarentena separada; exige respaldo,
ensayo revertido, hashes y postflight. Ese bloque no incluía modelos/interfaz; la integración posterior se documenta arriba.
[Contrato y operación](reactivacion_single_user/INGESTA_WNBA_2026-10-25.md).

## Scraper WNBA independiente — 2026-10-24

Nuevo extractor ESPN con plan predeterminado, ejecución explícita a JSONL/CSV,
contrato por partido, Q1–Q4/OT, estadísticas opcionales, UTC/Colombia, cuarentena,
reanudación verificada por SHA-256 y límites HTTP. Separa Commissioner’s Cup de REG.
Piloto acotado: cinco finales completos y estadísticas por ambos lados; no acredita
cobertura histórica total. Sin importación a BD, frontend WNBA, modelo ni cron;
NBA/Euroliga intactos. [Uso, revisión y validación](reactivacion_single_user/SCRAPER_WNBA_2026-10-24.md).

> **Estado operativo 2026-10-05:** AnalyticsPredict funciona localmente como herramienta personal single-user, sin login, pagos, suscripciones ni tiers. Neon fue migrada tras backup verificado: 182 apuestas NBA, 13 de fútbol, 7 combinadas y 16 selecciones conservadas. La configuración proviene de la cuenta con mayor actividad; por instrucción posterior del propietario, **todos** los registros deportivos son historial personal visible. La procedencia original permanece en el backup privado. `docs/reactivacion_single_user/` gobierna el trabajo nuevo. C0–C7 y la estrategia comercial descritos debajo son históricos, no tareas vigentes.

## Cierre de apuestas finalizadas — 2026-10-24

Bitácora añade **Completar finalizadas** para apuestas simples NBA/Euroliga/fútbol.
Cierre idempotente por dominio, sin reabrir completadas ni usar NULL como cero;
Euroliga sin OT y fútbol en regulación/mitades. Cuota legacy inválida permite
outcome verificable, pero importe NULL/N/D. Sin descarga implícita ni cron.
Reparación puntual autorizada con respaldo/rollback/postflight; sin modelos nuevos.
[Contrato, diagnóstico y validación](reactivacion_single_user/CIERRE_BITACORA_FINALIZADAS_2026-10-24.md).


## Paridad completa de análisis Euroliga y fútbol — 2026-10-23

Ganador (1X2 en fútbol), periodos propios, impacto/ajustes trazados, valor por cuotas,
riesgo, H2H, forma, historial y razones disponibles sin bloquear por certificación.
Euroliga conserva Ridge base y expone escenario heurístico de forma/descanso;
fútbol usa su predictor heurístico existente sin activar ML. Sin reparto ficticio
48/52, confianza ni descanso inventados. Sin POST productivo ni cambio de artefactos.
[Contrato, métodos y validación](reactivacion_single_user/PARIDAD_ANALISIS_DEPORTIVOS_2026-10-23.md).

## Qué es AnalyticsPredict hoy
Plataforma analítica de decisiones deportivas con foco operativo (calidad de datos, contratos API, métricas, política de operación y trazabilidad), no una app de picks masivos.

## Qué documento manda
1. `docs/FUENTE_DE_VERDAD_ACTUAL.md` (este archivo)
2. `docs/arquitectura/ESTADO_PROYECTO.md` (estado formal por bloques)
3. `docs/reactivacion_single_user/ROADMAP_REACTIVACION_ANALYTICSPREDICT.md` (plan vigente)
4. `docs/reactivacion_single_user/DEUDA_TECNICA_PRIORIZADA.md` (prioridades técnicas)
5. `docs/borlty-context/` (contexto histórico complementario)

### Guardado manual de apuestas fútbol — 2026-10-22

[Diagnóstico y validación](reactivacion_single_user/REGISTRO_MANUAL_APUESTAS_FUTBOL_2026-10-22.md): el botón de Bitácora ya no depende de
que exista una recomendación exacta. Se guarda la selección Over/Under válida,
con cuota del lado correcto y campos analíticos N/D cuando no están disponibles.
La lectura unificada existente incluye `apuestas_futbol`. Validación sintética
backend/frontend, lint/build verdes; sin POST ni cambios a apuestas productivas.

### Cuota y guardado de apuestas Euroliga — 2026-10-22

[Flujo y validación](reactivacion_single_user/REGISTRO_APUESTAS_EUROLIGA_2026-10-22.md): el modal Euroliga ahora acepta cuota decimal observada y stake, y crea un registro que queda identificado como EURO en la bitácora unificada. Competencia/fixture se validan en backend; probabilidad disponible se etiqueta RAW no calibrada y confianza/EV quedan NULL. La resolución automática y las métricas deportivas siguen siendo NBA (filas Euroliga excluidas). No se probó con apuesta productiva ni se tocó la base.

### Corrección de visibilidad del calendario fútbol — 2026-10-22

El selector de Fútbol consulta partidos desde el inicio del día local (`America/Bogota`) y admite estados activos (`EN_VIVO` y fases), además de los programados. Evita ocultar encuentros al pasar su hora de inicio. La lista conserva el estado que entrega la base; no hay refresco automático de marcadores ni se infiere que un partido está en juego solo por el reloj. Detalle/reproducción: [corrección y límites](reactivacion_single_user/VISIBILIDAD_CALENDARIO_FUTBOL_EN_CURSO_2026-10-22.md).

## Prioridades activas

### Modos NBA y resultados compartidos — 2026-10-22

[Uso, método y validación](reactivacion_single_user/MODOS_NBA_Y_RESULTADOS_2026-10-22.md): NBA añade prepartido y cortes completos Q1–Q3,
ruta live propia, validación consecutiva y dispersión solo de lo pendiente. Ajuste
de ritmo heurístico/RAW, sin entrenar ni usar calibración o cuotas PRE. El corte
es solo consulta y no contamina registros de apuestas/predicciones prepartido.
Euroliga usa el mismo componente completo de resultados NBA, con H2H/forma comunes,
RAW/push/regulación y datos ausentes explícitos. 36 pruebas backend focalizadas,
58 frontend/lint/build; sin POST productivo ni modificar artefactos/cohortes.
No acredita eficacia, calibración o actualización live por reloj.

### Historial detallado y diagnóstico Euroliga — 2026-10-22

[Alcance y validación](reactivacion_single_user/ANALISIS_EUROLIGA_DETALLADO_2026-10-22.md): cada análisis Euroliga incluye historial propio de hasta 50 finales previos por equipo, selector de 10/25/50 y sede, resultados/promedios de regulación, cuartos, OT y final separados, además de resumen de temporada local/visitante. Añade evaluación retrospectiva por periodo y trazabilidad del artefacto. Se presenta como descriptivo: la cohorte EVAL es del candidato congelado, no del refit final; no hay calibrador ni prospectiva independiente y sigue NO CERTIFICADO. No se llama a APIs ni modelos NBA ni se agregan cuotas, sizing o picks. Pruebas backend/frontend y lint/build verdes; inspección visual con datos sintéticos rotulados, sin POST productivo, DML o entrenamiento.

### Interfaz única Baloncesto — 2026-10-22

[Integración, uso y límites](reactivacion_single_user/INTEGRACION_UI_BALONCESTO_2026-10-22.md): una sección **Baloncesto** en
`/baloncesto`, selector NBA/Euroliga y formulario/layout del analizador NBA
compartidos. `/app` y `/euroliga` son redirecciones compatibles, no pantallas
separadas. Cada liga conserva catálogo, calendario, petición y predictor propios;
cambiar de liga limpia la selección y la salida anterior. Euroliga no llama al
análisis ni a temporadas NBA. Historial original sin repetir POST, regulación sin
OT y probabilidades RAW explícitas. 51 pruebas frontend, lint/build y visual real
desktop/móvil390px aprobados. Sin POST productivo, cambios de BD o modelos.
La integración visual no acredita calibración ni igualdad de eficacia.

### Predictor Euroliga integrado — 2026-10-21

[Uso, método y límites](reactivacion_single_user/PREDICTOR_EUROLIGA_2026-10-21.md). Pantalla `/euroliga`, API,
Ridge y artefacto propios; probabilidades RAW de cuartos/total de 40 min sin OT,
condicionamiento a Q1–Q3 completos y journal separado. 2.591 finales hasta21oct tras
una alta oficial 90–81 Hapoel–Virtus con rollback/postflight. NBA 2123 intacto.
Euroliga `euro-f9cc361e255b91196acc`, 29 entidades históricas,69 fixtures reconocibles.
EVAL 327/463: MAE total 15,9832 vs media 15,6727; sin superioridad acreditada ni calibración
del refit final. Cohorte 69/0 abstenciones, 63 anteriores por fecha, 0 outcomes; 6 del 22oct
sin hora de kickoff no acreditan prospectiva. 994 backend/42 frontend/lint/build y
visual desktop/móvil aprobados. Sin apuestas/registros NBA ni cron. Funcionalidad
integrada; eficacia NO_CERTIFICADA y no demostrada equivalente a NBA.


- **Aplicación puntual de matriz WEB — 2026-10-21:** por instrucción expresa del Jefe se persistieron internamente 11.991 campos NULL-only de 2.185 partidos de fútbol, con categoría `WEB`; proveedor y URL originales permanecen por observación. Se verificaron 4.559/4.559 identidades canónicas, respaldo privado, ensayo con rollback y postflight independiente. El censo bajó de 4.559/24.593 partidos y 26.144 celdas con NULL a **2.497 partidos/14.153 celdas**; 2.062 partidos pasaron a seis métricas pobladas. Se conservaron los valores no nulos, FT, apuestas y modelos; sigue habiendo **0 modelos de fútbol activos**. El Jefe indicó dejar el residual como NULL. No se consultaron páginas en esta aplicación ni se revalidó cada cifra contra su URL. El propietario suministró el lote y ordenó su uso privado; esto es una excepción de alcance puntual, no acredita licencia de los proveedores ni habilita nuevas extracciones/importaciones. Acta y hashes privados en `Carpeta de Entregas de Borlty/APLICACION_STATS_FUTBOL_WEB_2026-10-21/`.

- **Calendario de 30 días y estado de recuperación — 2026-10-21:** [corte y límites](reactivacion_single_user/PUESTA_EN_MARCHA_BASE_Y_CALENDARIOS_2026-10-21.md). Verificados 232 fixtures NBA (114 altas), 69 EuroLeague (69 altas) y 256 partidos de fútbol ya existentes en ocho competiciones; dos fechas futuras de fútbol actualizadas en las mismas filas. Los endpoints sirven 256 partidos de fútbol y 301 de baloncesto en el horizonte. Sin actualización automática. El censo estadístico READ ONLY de 15:19 UTC conserva 4.603/24.593 finales FT con NULL en seis métricas (26.414 celdas); no se añadieron estadísticas históricas en esta pasada. Términos públicos permiten uso interno de SportsAPI Pro Free, pero el GET autenticado exacto devolvió 403 y se detuvo sin reintento; UEFA se excluyó por sus términos contra recopilación para bases/software. Calendario listo en el horizonte verificado, base histórica incompleta y sistema NO CERTIFICADO.

- **Datos multi-fuente de fútbol, 20/10–21/10:** [censo, cruces y límites](reactivacion_single_user/RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20.md). Corte de crosswalk `REPEATABLE READ / READ ONLY` **2026-10-21 03:21:18 UTC** (histórico; el censo posterior de campos a 15:19 UTC se resume arriba): 24.593 finales FT, **4.603 partidos con NULL (26.414 celdas)**; gaps por código: ENG_FACUP 862, ESP_COPA 338, EUR_CHAMPIONS 336, EUR_CONFERENCE 968, EUR_EUROPA 796, FRA_COUPE 1.104 e ITA_COPPA 199. Neon registra **236 vínculos, 1.398 observaciones y 1.396 pares partido-campo**. Separación por fuente original: **97 ESPN_SOCCER** y **4.506 SOFASCORE**. Los 97 ESPN están auditados 97/97 y sus summaries no aportan estadísticas útiles. El cruce exacto del dataset HF CC-BY declarado produjo 800 candidatos de cinco competiciones, pero los 4.418 campos nulos de esos candidatos son ceros de calidad dudosa; hay 12 partidos con conflictos. Se rechazaron todos: **0 valores nuevos**. DataHub produjo 0 coincidencias adicionales. La conexión protegida de AnalyticsPredict funciona y sus permisos se comprobaron con metadatos dentro de una transacción READ ONLY; no se usó DDL/DML. Detalle técnico en evidencia privada. Regla: solo fuentes gratuitas con derechos/upstream claros; nada de pagos, trials, scraping contra términos o bypass. No hay fuente gratuita integral validada. Fuentes oficiales confirmaron ejemplos fuera de sus códigos (Fredrikstad–Molde, Copa Noruega, bajo ENG_FACUP; Sporting–Nacional, Allianz Cup/Taça da Liga, bajo ITA_COPPA). `pais_id` faltante impide estimar extensión; no imputar país ni recategorizar. Evidencia privada: `HF_CROSSWALK_2026-10-20/ACTA_NEON_Y_CROSSWALK_HF_2026-10-20.md` y `ACTA_PRIVILEGIOS_NEON_READONLY_2026-10-20.md`.

Actualización inicial 2026-10-21 03:02 UTC: se midió localmente `eatpizzanot/soccer-dataset` (CC-BY-4.0 declarada, con salvedades de derechos upstream). La consulta Neon READ ONLY autorizada posterior y el crosswalk exacto de las 03:21 UTC identificaron 800 candidatos; **no son 800 recuperaciones**. Los 4.418 campos canónicos nulos dentro de esos candidatos son ceros fuente de calidad dudosa, y 12 partidos presentan conflictos. Cero valores positivos verificables completaron esos NULL; DataHub añadió cero coincidencias. Se rechazó el lote completo y Neon no se modificó. Detalle y hashes en `HF_CROSSWALK_2026-10-20/`.

Prueba autenticada limitada de SportsAPI Pro (21/10 04:22 UTC): Chrome normal ya mostraba una cuenta verificada en plan Free (100 requests/día, billing “Free forever”); la API key se guardó en el Secret Store protegido como `SPORTSAPIPRO_API_KEY`, limitada a `api.sportsapipro.com`. Se contabilizaron 44 GET. Temporadas y una página de 30 fixtures dieron HTTP 200 en siete competencias residuales. En seis muestras 2025/26 de UCL, UEL, Conference, Copa del Rey, Coupe de France y Coppa Italia, stats devolvió cinco claves objetivo/componentes en `ALL`, `1ST`, `2ND`; las identidades aritméticas de tiros y periodos conciliaron. FA Cup respondió 200, pero la evidencia visible solo conserva `ALL`/`1ST`. Esto acredita muestras técnicas, no cobertura completa ni cruces con NULLs. La respuesta `source: live` no identifica el upstream; falta validar procedencia/derechos y hacer un crosswalk exacto antes de considerar backfill. **Neon no se consultó ni modificó y no se importaron datos.** Evidencia privada `REGISTRO_SPORTSAPI_PRO_2026-10-20/`.

Reconsulta pública HF — 21/10 03:34 UTC: los metadatos API no listan datasets para `corner football`, `shots soccer` ni `football statistics cup`. No es prueba de inexistencia global. Sin descarga ni consulta/escritura a Neon; el censo sigue en 03:21:18 UTC hasta otro recenso. Evidencia externa `FUENTES_GRATUITAS_RECHECK_2026-10-20/`.

Actualización de catálogo gratuito — 21/10 02:31–02:36 UTC: StatsBomb shots en HF carece de corners y no amplía el crosswalk ya auditado; Football Charts y el repo de resultados UCL no publican las seis métricas; Match-Data se atribuye a upstreams sin derechos independientes acreditados y solo enumera ligas; FA Cup Hub tampoco lista tiros/córners y su `/api/` está desautorizado por robots.txt. Kaggle y una consulta de búsqueda mostraron desafíos que no se resolvieron. Sin nuevas escrituras ni valores; censo sigue como referencia READ ONLY 01:59:43 UTC (4.603/24.593, 26.414 celdas). Evidencia privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_CATALOG_CONTINUATION_20261021T0236Z.json`; CI `1d18751` 4/4 verde.


Barrido de catálogos públicos 21/10 02:12 UTC: tres búsquedas HF sin resultados; OpenAIRE no listó datasets para FA Cup y su búsqueda UEFA mostró cuatro registros no pertinentes. Figshare expone un corpus de eventos Wyscout para cinco ligas y dos torneos de selecciones, no copas de clubes. DataCite mostró estadísticas de ligas principales sin cobertura de copas. La página oficial de football-data.org confirma que su plan gratis no contiene estadísticas y el add-on de corners/tiros cuesta €15/mes; queda excluido. API-Football devolvió challenge HTTP 403 y no se reintentó. Ningún valor nuevo ni DDL/DML; censo sigue siendo el READ ONLY de 01:59:43 UTC. CI de `83f8a0b` pasó 4/4. Evidencia privada con raws y hashes: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/PUBLIC_CATALOGS_TARGETED_20261021.json`.

Revisión histórica de fuentes: Sportmonks, StatPal/SoccerDataAPI, Goalserve, Stats API y Footballdata.io no demostraron acceso gratuito abierto con cobertura/retención compatible para los gaps; quedan excluidas, no son opciones vigentes. Se excluye también `vsntll/xValue` por licencia de datos ausente y restricciones de FotMob. No se crearon cuentas, claves o pruebas. Evidencia histórica en `SPORTMONKS_SOURCE_AUDIT_2026-10-20/`; no hubo valores nuevos.

Ampliación de catálogo 20/10: `xgabora/Club-Football-Match-Data` anuncia 38 códigos de liga/división y licencia MIT del repositorio, pero atribuye sus estadísticas al upstream Football-Data.co.uk; no se confirmó una licencia separada de los datos ni cobertura de copas UEFA/nacionales. Los resultados revisados en Hugging Face/Zenodo eran ligas top-5, resultados/minutos de gol, un dataset UEFA no comercial y estrecho, o carecían de procedencia/licencia suficiente. No se descargaron esos CSV. Se evaluó in-memory una muestra HF de 20 partidos UEFA: 5 tenían stats, pero solo 2 coincidieron con partidos canónicos y ambos ya estaban completos; 3 no tuvieron match canónico en ±1 día. El producto completo del vendedor es de pago, bajo licencia `single-commercial-user`, cubre UCL/UEL/Conference pero no copas nacionales; el README dice que la mayoría de las clasificatorias UEFA no se incluyen. El campo `Goal_Attempts` no tiene equivalencia documentada a tiros totales. Queda excluido por la instrucción posterior del propietario de usar únicamente fuentes gratuitas; no hubo compra, trial ni valores aplicados. El último censo observado continúa siendo el READ ONLY de 23:59 UTC (4.605 partidos/26.426 celdas con NULL); la consulta puntual `READ ONLY` no modificó Neon ni recalculó el censo. Evidencia privada `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/`.

Continuidad 21/10: el sample gratuito de Sports Data Vault no contiene estadísticas en sus 32 partidos de clasificación de FA Cup y no presenta encuentros de las otras copas/torneos europeos residuales; no se importó. TheStatsAPI queda fuera hasta validar sus fixtures de muestra y compatibilidad de retención con la base/modelos. API-Football y Sportmonks mantienen cobertura promocional pero requieren autenticación para comprobar temporadas/fixtures; no se crearon cuentas, trials ni claves. Sin nueva consulta/escritura a Neon; el último censo observado sigue en 4.605/24.593 partidos y 26.426 celdas NULL. Evidencia: `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/CATALOG_AUDIT_SUPPLEMENT_20261021.json`; acta de entrega `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/ACTA.md`.

**Restricción operativa aclarada por el propietario (21/10): solo fuentes gratis, sin prueba que pueda convertirse en cobro.** Las referencias de precios anteriores quedan como descartes históricos; no se contratará ni pagará proveedor. Se comprobaron las páginas CSV de FootyStats para copas/UEFA: publican conteos por temporada, pero el único sample anunciado sin registro es EPL 2018/19, ampliar descargas consume créditos y los términos prohíben acceso/extracción automatizados salvo autorización por API; no se usará para completar esta BD. StrikerAPI anuncia 500 créditos gratis mensuales sin tarjeta y permite almacenamiento/modelado bajo sus términos, pero exige cuenta y email verificado, declara que sus datos derivan de ESPN, no enumera las copas nacionales objetivo y advierte que las clasificatorias UEFA suelen estar sin boxscore. No valida los gaps restantes ni una solución integral; no se creó cuenta ni se hizo llamada. Datasets libres nuevos revisados fueron solo resultados/fixtures, duplicados de la fuente HF ya auditada, de una fase UEFA que no presenta gaps, o sin licencia/procedencia suficiente. Sin clave, pago, trial, descarga nueva, cuenta, cambio en Neon ni valores nuevos; el censo observado sigue siendo 4.605/24.593 partidos con NULL (26.426 celdas) del 20/10 23:59 UTC. Evidencia resumida: entrega privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

Ampliación READ ONLY del 21/10 01:59:43 UTC: FPL Core Insights publica 85 CSV por torneo para UEFA/EFL Cup 2025/26–2026/27 y su README invita a reutilizar con atribución, pero no declara licencia SPDX; los registros usan IDs/URLs de FotMob y no se acreditó permiso upstream. El cruce estricto de sus 116 filas finalizadas/estadísticas procesadas dio 35 pares exactos de alias en alguna fecha, 0 dentro de ±1 día y 0 partidos canónicos únicos con FT coincidente; no aporta NULLs existentes y no se importó. Harvard Dataverse ofrece un archivo CC0 con resultados/composición de planteles, sin corners/tiros/SOT; su otro depósito UCL/UEL no lista archivos públicos. Mendeley falló hidratación de la interfaz y mostró resultados genéricos; Zenodo y GitHub repo-search devolvieron 403 y no se reintentaron. Sin cambios de Neon. Evidencia: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/CATALOGS_FPL_HARVARD_MENDELEY_GITHUB_20261021.json`.

La búsqueda pública ampliada encontró un candidato con estadísticas de copas/UEFA en Kaggle (`ivanposinovec/football-matches-from-europe-and-south-america`) y otro con clasificatorias UCL 2020–2026. Ambos quedan excluidos: el primero declara scraping de FBref y aceptación de términos de Sports Reference pese a la etiqueta CC0 del espejo; el segundo tiene licencia “Other” y no aclara fuente/upstream ni permiso persistente. El dataset Wyscout CC BY 4.0 está limitado a top-five leagues 2017/18 y torneos de selecciones, no a los gaps objetivo; su descarga de 3,23 GB no se justificó. No se descargaron estos candidatos. El resto son estadísticas de otra copa/temporada, métricas parciales, resultados sin stats o agregados. Ninguna fuente gratuita con derechos claros ha cubierto todo el residual; no se cambió Neon. Evidencia `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

Revisión adicional 21/10 02:24 UTC: CI del commit `90b5973` pasó 4/4 (run `39531836396`). Un repo de GitHub anuncia 238.858 partidos/38 códigos de liga con corners, tiros y tiros al arco; su README atribuye el CSV a Football-Data.co.uk, no se acredita una licencia upstream separada y la cobertura documentada es de ligas/divisiones, no las copas/UEFA residuales. No se descargó el CSV de 45 MB. Otros resultados eran un proyecto UCL sin CSV/licencia de datos y una guía de proveedores sin licencia, no datasets. El buscador OpenClaw carece de clave Gemini; Google mostró `/sorry` y la lectura de Brave agotó timeout tras un reintento. Se respetaron esas barreras. Sin datos nuevos, cuentas, pagos ni DDL/DML; el censo de referencia sigue siendo READ ONLY `2026-10-21 01:59:43 UTC` (4.603/24.593; 26.414 celdas). Evidencia externa privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/GITHUB_FREE_STATS_REPOSITORY_REVIEW_20261021T0224Z.json`.

Barrido HF 21/10 02:27–02:28 UTC: `football match` listó 17 datasets, `soccer stats` 1 y `football cups` 0. Revisados los candidatos con licencia/campos aparentes: CC-BY top-5/UCL contiene resultados/HT/FT sin corners/tiros; la muestra CC-BY-NC es generada y de cinco equipos; los MIT recientes no documentan upstream/cobertura; mirrors duplican el Football-Data.co.uk ya excluido; el resto es fútbol robótico, un dataset vacío, resultados top-5 o productos pagos. La ficha JulienDelavande/Apache-2.0 describe resultados FBref, ratings SoFIFA y cuotas, no estadísticas de partido objetivo. Ninguno se descargó. Sin valores nuevos ni cambios en Neon. CI de `0bd75d0` pasó 4/4 (run `39533085455`). Evidencia privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/HF_BROAD_FOOTBALL_CATALOG_REVIEW_20261021T0229Z.json`.

- **ML fútbol V4,19/10:** [desarrollo y cohorte futura](reactivacion_single_user/ML_FUTBOL_FORMA_V4_2026-10-19.md).
  Selección temporal entre identidad/forma/híbrido, refit final explícito y recarga
  sin entrenar. Desarrollo exploratorio goles/disparos:1.157/1.193pares,96,98% de
  cobertura y mejora frente a baseline de liga; no prueba del artefacto final.
  Congelados251futuros por familia de goles/disparos antes del20/10; córners223/251,
  techo88,84%<90. Sin DML, activación, probabilidades ni cron;0MLfútbol activos.
  V1/V2/V3 intactas. Serving/calibración/promoción siguen pendientes de evidencia.

- **Flujo personal para empezar a usarlo (19/10):** en `/futbol` se puede elegir
  un partido, consultar el análisis/contexto disponible y guardarlo con “Guardar
  para revisar”; `/bitacora` mantiene una lista aparte con enlace para reabrirlo,
  incluso si ya salió del calendario próximo. Es un marcador neutral: no crea
  apuesta, pick ni probabilidad y se excluye de conteos/métricas de apuestas. El
  modelo ML de fútbol sigue sin estar activo. Ver entrega externa
  `PARTIDOS_GUARDADOS_BITACORA_2026-10-19`.

- **Datos actualizados 18/10:** [enero–octubre](reactivacion_single_user/ACTUALIZACION_INTEGRAL_DATOS_2026-10-18.md). Contrastados 2.928 finales de 12 competiciones fútbol, NBA y Euroliga: 273 altas/108 actualizaciones fútbol, 18 altas/6 fases NBA y 183 altas Euro. Neon con permisos efectivos suficientes, respaldos/rollback/postflight; 11 huellas protegidas intactas. Totales fútbol 25.118 (24.593 finales FT), NBA 10.379, Euro 2.672. Este corte prevalece para datos; no reentrena ni activa modelos, no resuelve prospectiva y no certifica eficacia. Refresco puntual, no cron.

- **Uso local verificado16/10:** [arranque visual/H12](reactivacion_single_user/ARRANQUE_VISUAL_Y_USO_LOCAL_2026-10-16.md): rutas visibles con datos, formulario fútbol aislado y análisisNBA interno con fase/corte;854backend/36frontend, audit0.15capturas/9outcomesPRE/0independientes; sinMLfútbol activo ni certificación. TicketH4cerrado por proveedor, sin purga. Este corte prevalece sobre estados visual/H12/outcomes anteriores.
- **Paquete integral estacional16/10:** [V2 de laboratorio y fases NBA](reactivacion_single_user/VALIDACION_ESTACIONAL_Y_FASES_NBA_2026-10-16.md). Candidatos futuros separados de V1, abstenciones/mínimos y evidencia temporal; PRE conservada y visible. Recuperación histórica solo con respaldo/ensayo, colisiones retenidas. Visual/H12/Git y certificación no se cierran por preparación técnica.
- **Siete frentes ejecutados16/10:** [resultados y dependencias](reactivacion_single_user/SIETE_FRENTES_2026-10-16.md). Complementados200finales con goles/córners1T/2T acreditados y postflight;618EVAL por familia, ninguna apta. M12 descriptivo ejecutado, no certificación. H4ensayo integral hecho, no purga remota; visual/H12 y outcomes conservan bloqueos explícitos.
- **Cierre técnico M04/M05,16/10:** [KPI/P&L y GET](reactivacion_single_user/KPI_PNL_Y_GET_2026-10-16.md): política monetaria común sin soportes/N/D, cohortes/grano, guardas GET/HEAD y fallos sanitizados; auditoría78GET. No certifica eficacia ni cierra M12, visual, fuentes, H4/H12 o prospectiva.
- **Avances16/10:** [calibración](reactivacion_single_user/KPI_CALIBRACION_2026-10-16.md) API/UI separa series/muestras/N/D sinTTL; [H12parcial](reactivacion_single_user/H12_DEPENDENCIAS_2026-10-16.md) reduce dev10→5altas/prod0. Ninguno cierra KPIintegral/H12 ni recertificación.
- **Corte consolidado2026-10-16:** estado/roadmap/deuda distinguen cierres y pendientes sin adendas contradictorias. [Evaluación temporal fútbol](reactivacion_single_user/EVALUACION_TEMPORAL_FUTBOL_2026-10-16.md) ejecutada; ninguna familia apta para activar, sin modelos nuevos enNeon. SoportesP&L no existen por confirmación del propietario: exclusión/N/D, no tarea humana. Seguir validación científica M12, H12, visual y fuentes; prospectiva requiere outcomes posteriores.
- Seguir las instrucciones más recientes del propietario y el roadmap single-user.
- H7 y la base de reproducibilidad/CI se verificaron con pruebas dirigidas y CI alojada (4/4 jobs, 2026-10-06). La recertificación analítica **no pasó**: ver `docs/reactivacion_single_user/RECERTIFICACION_ANALITICA_2026-10-06.md` antes de citar métricas de rendimiento.
- Para semántica analítica vigente, consultar `docs/reactivacion_single_user/CATALOGO_KPI_CANONICO_2026-10-06.md`, `VISTAS_ANALITICAS_CANONICAS.md` y `MAPA_SEMANTICO_DEL_SISTEMA.md`; los homónimos de `borlty-deliverables` son propuestas históricas.
- Mantener estado y changelog al cerrar bloques; el plan comercial y sus órdenes son históricos.

## Estrategia comercial histórica (C0; no vigente)
- Camino principal de caja: `C0 -> C1 -> C2 -> C3 -> C4 -> C7`.
- Camino paralelo controlado: `C5 -> C6` (no bloquea primer peso).
- NBA = frente comercial principal.
- Fútbol = **beta global con madurez diferenciada por mercado** (gobernado por scorecards walk-forward, política formal, monitoreo continuo y shadow mode).
- Regla vigente: no hay salida beta global automática; la promoción es parcial y reversible por mercado.
- Estado de cierre de etapa (bloques 10-14): **0 mercados promocionables** en la evidencia actual, por lo que fútbol mantiene beta global.
- No se posiciona el producto como app masiva de picks ni promesa de ganancias fáciles.

## Bloqueo comercial histórico (auditoría; no aplica al producto actual)
- C1 permanece **EN_CURSO** hasta ejecutar validación manual real de MercadoPago con dominio/URL pública final y callback estable.
- C7 permanece **PENDIENTE** y no se abre hasta cierre manual real de C1 (no aplica cierre por validación equivalente únicamente).

## Qué está en laboratorio
- Líneas no cerradas por criterios formales en `ESTADO_PROYECTO`.
- Funcionalidades con evidencia parcial en `docs/borlty-deliverables/` (reportes, pruebas de ciclo, validaciones puntuales).

## Qué se considera histórico
- `docs/archive/` → contexto obsoleto o reemplazado.
- Entregables cerrados y evidencia histórica viven en `docs/borlty-deliverables/`.

## Dónde consultar evidencia
- Reportes de ejecución/ciclos: `docs/borlty-deliverables/reportes/`
- Cierres por bloque: `docs/borlty-deliverables/bloque_08/`, `docs/borlty-deliverables/bloque_09/`
- Checklists históricos: `docs/borlty-deliverables/checklists/`

## Regla de gobierno documental
- Contexto activo debe mantenerse corto y gobernable.
- Entregables/evidencia no se borran; se preservan en `borlty-deliverables`.
- Lo obsoleto se archiva en `archive`.
