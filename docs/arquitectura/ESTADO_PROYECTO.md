# Estado vigente — AnalyticsPredict

Última actualización: **2026-10-21**. Herramienta personal single-user, local y
ligada a loopback. Sin login, pagos, suscripciones, tiers ni lanzamiento comercial.
Responsable operativo: UNIVERSIDAD21. Dictamen analítico: **NO CERTIFICADO**.

## Fuentes y continuidad

- [Fuente de verdad](../FUENTE_DE_VERDAD_ACTUAL.md).
- [Roadmap vigente](../reactivacion_single_user/ROADMAP_REACTIVACION_ANALYTICSPREDICT.md).
- [Deuda priorizada](../reactivacion_single_user/DEUDA_TECNICA_PRIORIZADA.md).
- [Checklist de uso](../reactivacion_single_user/CHECKLIST_PREPARACION_USO_2026-10-15.md).
- [Siete frentes, fuentes por mitades y validación](../reactivacion_single_user/SIETE_FRENTES_2026-10-16.md).
- [KPI/P&L y auditoría GET](../reactivacion_single_user/KPI_PNL_Y_GET_2026-10-16.md).
- [KPI de calibración](../reactivacion_single_user/KPI_CALIBRACION_2026-10-16.md).
- [Evaluación temporal fútbol](../reactivacion_single_user/EVALUACION_TEMPORAL_FUTBOL_2026-10-16.md).

## Recuperación multi-fuente de nulos — 2026-10-20

[Estado, cobertura y límites](../reactivacion_single_user/RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20.md).
Transacción vigente **REPEATABLE READ / READ ONLY 2026-10-21 03:21:18 UTC:** 24.593
finales FT; **4.603 partidos con algún NULL (26.414 celdas)** en las seis métricas. Por
código interno: ENG_FACUP 862; ESP_COPA 338; EUR_CHAMPIONS 336; EUR_CONFERENCE 968;
EUR_EUROPA 796; FRA_COUPE 1.104; ITA_COPPA 199. Persisten 236 vínculos, 1.398
observaciones y 1.396 pares partido-campo. Por fuente original: **97 ESPN_SOCCER** y
**4.506 SOFASCORE**. Los gaps ESPN están auditados 97/97 y sus summaries no contienen
estadísticas útiles. El snapshot HF CC-BY declarado se cruzó exactamente: 800
candidatos en cinco competiciones, pero los 4.418 campos faltantes de esos candidatos
son ceros literales de calidad dudosa; además se detectaron 12 partidos con conflictos.
DataHub dio 0 coincidencias adicionales. No se aplicaron valores en este corte. La
conexión protegida de AnalyticsPredict a Neon funciona; el censo y la consulta de
metadatos de permisos se ejecutaron en transacciones READ ONLY, sin DDL/DML. La
integración Neon de OpenClaw apuntaba a otro proyecto y no se usó. La evidencia
detallada de permisos queda fuera del repositorio en
`HF_CROSSWALK_2026-10-20/ACTA_PRIVILEGIOS_NEON_READONLY_2026-10-20.md`.

El lote gratuito anterior aplicó 12 campos a dos partidos Coupe de France con backup,
rollback y postflight; los FT canónicos permanecen intactos. No hay una fuente gratuita
integral validada. No contratar, pagar, abrir trials ni crear cuentas/claves; no
extraer sitios con términos incompatibles ni eludir 403/CAPTCHAs. Se confirmaron
ejemplos fuera de su código: Fredrikstad–Molde (Copa Noruega) bajo ENG_FACUP y
Sporting–Nacional (Allianz Cup/Taça da Liga) bajo ITA_COPPA. `pais_id` faltante impide
estimar el alcance; esas distribuciones no equivalen a conteos de FA Cup/Coppa Italia
reales. No imputar países ni recategorizar en este corte. Evidencia privada en
`SOURCE_SPLIT_AND_FREE_CROSSWALK_20261021T014525Z.json`,
`GITHUB_HTML_FREE_SOURCE_SEARCH_20261021T0148Z.json` y
`COMPETITION_CROSSWALK_FREE_SOURCE_REVIEW_20261021T0135Z.json`.

**Auditoría HF 2026-10-21 03:02–03:23 UTC:** el archivo local
`eatpizzanot/soccer-dataset` anuncia CC BY 4.0 y enumera API-Football y
football-data.co.uk como upstreams, sin que esa declaración resuelva por sí sola sus
derechos. La consulta Neon READ ONLY posterior cotejó 800 fixtures por nombres exactos
normalizados, localía, FT, mismo día y unicidad. Aunque 788 no chocan con valores
existentes, sus 4.418 campos objetivo nulos son ceros de fuente; 12 fixtures tienen 13
discrepancias, 12 ceros contra positivos y una diferencia 4 vs. 6. Se rechazó el lote
completo, incluidos positivos aislados dentro de fixtures conflictivos. DataHub produjo
0 cruces. Neon recibió cero valores nuevos. Crosswalk y adjudicación en la entrega
privada `HF_CROSSWALK_2026-10-20/`, con manifiesto SHA-256.

Lead gratuito revisado 21/10 03:27 UTC: SportsAPI Pro publica Free (100 requests/día,
sin tarjeta), acceso declarado a todos los endpoints/competiciones y retención interna
para análisis/modelado. El catálogo documentado expone corners y componentes de
disparo, pero no una definición suficiente para todos los seis campos; además declara
profundidad menor en lower/basic tiers, no acredita todas las copas/temporadas y sus
endpoints requieren API key (401 en las consultas sin autenticar). El formulario Free
solicita nombre, email, contraseña y aceptación de términos; no se envió información,
no se aceptaron términos ni se creó cuenta/descargaron datos. Es un candidato
condicionado, no una fuente probada. Evidencia externa
`APISPORTSPRO_CANDIDATE_AUDIT_2026-10-20/`.

Ampliación de búsqueda a las 02:12 UTC en catálogos públicos: Hugging Face sin
datasets para tres consultas focales; OpenAIRE sin resultados de datasets FA Cup y
cuatro registros UEFA no pertinentes; Figshare/Wyscout enumera solo top-5 europeas y
torneos de selecciones; DataCite devuelve datasets de ligas principales, no de las
copas objetivo. La oferta gratis de football-data.org excluye estadísticas y anuncia
corners/tiros en un add-on pagado; no se usa. API-Football volvió a responder challenge
403 y la ruta se dejó detenida. No hay valores nuevos ni mutación de Neon. Evidencia
privada con respuestas y hashes `PUBLIC_CATALOGS_TARGETED_20261021.json`; CI de
`83f8a0b` verificado 4/4 verde.

Los antecedentes de búsqueda y excepciones de fuente permanecen abajo como cortes
históricos con su fecha; no reemplazan el censo ni la decisión más reciente.
Sin ML fútbol activo, apuestas/modelos alterados o ingestas programadas.
Actualización de fuentes 21/10 02:36 UTC: las fichas públicas nuevas no cubren métricas+competiciones residuales con derechos claros. Censo no actualizado desde 01:59:43 UTC; no hubo escrituras ni valores. Evidencia externa `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_CATALOG_CONTINUATION_20261021T0236Z.json`. CI `1d18751` 4/4 verde.


La búsqueda adicional de catálogos públicos GitHub/Hugging Face/Zenodo tampoco
acreditó cobertura/licencia suficiente para las copas nacionales o clasificatorias
UEFA pendientes. El repo `xgabora/Club-Football-Match-Data` declara MIT para el
repositorio, pero atribuye sus estadísticas a Football-Data.co.uk y documenta
códigos de ligas/divisiones, sin confirmar derechos upstream ni cobertura de copas.
Otros resultados eran top-5, solo marcadores/minutos de gol, licencia no comercial
o procedencia insuficiente. Se evaluó in-memory una muestra comercial de 20 partidos
UEFA: solo 2 coincidieron con registros canónicos y ambos tienen las seis métricas;
los otros 3 no existían en la base dentro de ±1 día. El producto completo es de pago,
con licencia single-commercial-user; incluye UCL/UEL/Conference desde 2016, pero no
copas nacionales y declara que la mayoría de clasificatorias no están cubiertas.
`Goal_Attempts` no tiene semántica documentada equivalente a tiros totales. Queda
excluido por la instrucción posterior del propietario de usar únicamente fuentes
gratuitas, no es candidato vigente. No hubo compra, trial, ni persistencia de la
muestra. La consulta puntual READ ONLY no recalculó el
censo ni escribió. El último censo observado es 4.605/24.593 partidos con NULL
(26.426 celdas) al 2026-10-20 23:59 UTC. Evidencia: entrega privada
`FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/`.

**Criterio del propietario para nuevas fuentes (21/10): exclusivamente gratuitas, sin trial convertible ni pago.** FootyStats lista CSV por temporada para varias copas/UEFA, pero la descarga ampliada requiere créditos; su sample sin registro es solo EPL y los términos prohíben extracción automatizada del sitio. Se excluye. StrikerAPI da 500 créditos mensuales sin tarjeta y permite almacenar/modelar bajo términos publicados, pero requiere cuenta verificada, consume cuota, usa ESPN como upstream, no enumera las copas nacionales pendientes y declara que las clasificatorias UEFA suelen no tener boxscores. No se probó con clave ni ofrece cobertura demostrada de los gaps actuales. Se descartan asimismo espejos o repos sin autorización/upstream claro, aunque el repositorio declare licencia de código. Sin nuevas cuentas, claves, compras, pruebas, consultas o escrituras; último censo sin cambios: 4.605/24.593 finales FT con al menos un NULL (26.426 celdas, observación 2026-10-20 23:59 UTC). El análisis sigue abierto, no hay fuente gratuita verificada que cubra todo el residuo. Evidencia: entrega externa `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

Cotejo adicional READ ONLY (2026-10-21 01:59:43 UTC): FPL Core Insights GitHub expone 85 CSV por torneo, pero sus 116 filas finalizadas/procesadas no enlazan a ningún partido canónico actual por equipos, fecha ±1 y FT; **0 nuevos valores**. El README permite reutilización con atribución, aunque no hay licencia SPDX y no se acreditó upstream FotMob, por lo que se excluye. Un depósito CC0 de Harvard contiene resultados y covariables de plantilla, no las seis métricas; otro registro UCL/UEL no publica archivos. Mendeley UI tiene errores React y resultado genérico; GitHub repo-search y Zenodo API respondieron 403, respetados sin reintento/bypass. Censo observado sin cambio: 4.603/24.593 (26.414 celdas). Acta/evidencia privada: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/CATALOGS_FPL_HARVARD_MENDELEY_GITHUB_20261021.json`. Sin DDL/DML, claves, cuentas ni pagos.

Catálogo gratuito ampliado (21/10): Kaggle lista `ivanposinovec/football-matches-from-europe-and-south-america` como CC0 y declara estadísticas de copas/UEFA 2015–2023, pero el propio registro dice que scrapea FBref y somete su uso a términos de Sports Reference; no se descargó ni se usará sin permiso claro. Un dataset UCL 2020–2026 que anuncia estadísticas de clasificatorias marca la licencia como “Other” y no aclara upstream ni retención; también excluido. El Wyscout CC BY 4.0 es de ligas top-five 2017/18 más torneos nacionales, no copas/UEFA de clubes, y sus archivos de 3,23 GB no se descargaron. Los demás resultados no cubren las métricas/competencias pendientes. No se pagó, no se inició trial/cuenta y no cambió Neon. Evidencia de catálogo y hashes en `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

Revisión GitHub 21/10 02:24 UTC: `xgabora/Club-Football-Match-Data` declara 238.858 filas, 38 códigos de liga/división y las seis métricas, pero su README atribuye el dataset a Football-Data.co.uk y no confirma licencia independiente del upstream ni cobertura de las copas/clasificatorias residuales. No se descargó el CSV. Un proyecto UCL adicional no publica el CSV anunciado ni licencia de datos; una guía de fuentes tampoco es dataset. Google activó `/sorry`, Brave expiró tras un reintento y el buscador OpenClaw sigue sin clave Gemini; no se cambiaron configuración ni credenciales. CI de `90b5973` verde 4/4 (run `39531836396`). Sin nuevos valores ni DDL/DML; censo de referencia sigue en 4.603/24.593 (26.414 celdas, READ ONLY 01:59:43 UTC). Evidencia: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/GITHUB_FREE_STATS_REPOSITORY_REVIEW_20261021T0224Z.json`.

Catálogo HF 21/10 02:27–02:28 UTC: 17 resultados `football match`, uno `soccer stats`, cero `football cups`. Las fichas de datos gratuitos compatibles se acotan a resultados/HT/FT (sin las seis métricas), ligas top-5 ya completas, muestras generadas o sin upstream/licencia verificable; duplicados y ofertas pagas se excluyeron. No se descargó ningún CSV. CI de `0bd75d0` pasó 4/4 (run `39533085455`). Evidencia privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/HF_BROAD_FOOTBALL_CATALOG_REVIEW_20261021T0229Z.json`; sin DDL/DML, cuentas, pagos ni nuevos valores.

## Corte vigente de datos — 2026-10-18

[Actualización integral enero–octubre](../reactivacion_single_user/ACTUALIZACION_INTEGRAL_DATOS_2026-10-18.md):
2.928 finales de fuentes contrastados, sin faltantes en esa cohorte. Fútbol +273
partidos/108 actualizaciones (82 estados programados cerrados y 26 conciliaciones);
NBA +18/6 fases; Euroliga +183. Totales 25.118 fútbol/24.593 finales FT,
10.379 NBA y 2.672 Euro. Un desglose de periodos inválido del proveedor se conserva
NULL, no imputado. Backups, rollback, idempotencia y once huellas protegidas intactas;
875 backend y 36 frontend aprobadas, lint/build/audit producción 0.
Fútbol sin ML activo, NBA 2123 sin reentrenar, prospectiva 15/9/0 independientes
sin modificar. Servicios no arrancados por esta tarea; no cron ni certificación.
Las cifras y límites analíticos del 16/10 siguientes son antecedentes de sus
cohortes; no se han recalculado ni trasladado a esta nueva base.

## Flujo inicial de uso — 2026-10-19

`/futbol` permite seleccionar un partido y consultar los datos/análisis
disponibles; “Guardar para revisar” lo agrega a una lista separada dentro de
`/bitacora`, desde donde se vuelve a abrir por su UUID. Guardar/reabrir no crea
una apuesta, mercado, pick ni probabilidad. El estado neutral queda fuera de
conteos, métricas, evaluaciones y backfill de apuestas. La implementación no
requiere DDL; solo escribe cuando el propietario pulsa guardar o quitar. Modelo
ML fútbol continúa sin activo; la certificación global permanece **NO CERTIFICADO**.
Detalle y pruebas dirigidas en la entrega externa
`PARTIDOS_GUARDADOS_BITACORA_2026-10-19`.

## Desarrollo ML fútbol V4 — 2026-10-19

[Protocolo, resultados y límites](../reactivacion_single_user/ML_FUTBOL_FORMA_V4_2026-10-19.md).
Nuevos candidatos Ridge con forma causal/contexto de liga y refit final anterior
a eventos futuros, separados de V1/V2/V3. Desarrollo retrospectivo:1.157/1.193
pares goles/disparos,96,98%cobertura, mejora frente a baseline de liga y sin targets
nominalmente peores; esto NO certifica el refit final ni reescribe los gatesV1.
Córners619/1.193,51,89%, no apto por cobertura. Cohorte futura20oct–1dicUTC:
251partidos,251predicciones goles/251disparos/223córners+28abstenciones, techo
córners88,84%<90. Estado inicial0pares/N/D, sin calibrador ni activación.
JSONcoeficientes/features/estado/hash completo y CLI de evaluación posterior,
archivos externos no sobrescribibles.887backend/0fallos/0skips, dos deprecaciones;
CI y publicación delSHA final en acta externa. Neon soloREADONLY,0MLfútbol activos,
serving/NBA/apuestas/bitácora intactos. No cron, ingesta ni arranque de servicios.

## Corte de uso local y visual — 2026-10-16

[Arranque, correcciones y límites](../reactivacion_single_user/ARRANQUE_VISUAL_Y_USO_LOCAL_2026-10-16.md).
Backend/frontend loopback,2123/30equipos sin reentrenar; flujos visibles y formulario
fútbol sintético verificados. H12Tailwind4/audit0,854backend/36frontend/lint/build;
publicación/CI final acreditadas en acta externa. Estado15capturas/9outcomesPRE/
0independientes;6pendientes, sin repetir congelamientos. H4ticket#4868445cerrado
por proveedor con autoservicio, sin coordinación de purga. Fútbol0MLactivos y
P&LN/D; eficaciaNO_CERTIFICADA. Este corte reemplaza bloqueos visual/H12 y conteos
outcomes anteriores, no los cierres científicos aún pendientes.

## Última pasada integral anterior — 2026-10-16

[Detalle y límites](../reactivacion_single_user/VALIDACION_ESTACIONAL_Y_FASES_NBA_2026-10-16.md):
426finales recuperados con goles por mitades/FT/tiros,38colisiones retenidas,
163programados de noviembre sin marcadores, total24.845fútbol. No se incorporan
nuevos córners por mitades;358rechazos de conciliación conservados. Postflight
reconciliado con trigger genéricoFT sin corregir datos. V1sigue no apta.
V2futura199partidos:163predicciones/36abstenciones por familia, techo81,91%;
V3CAL100:88/78efectivos<100, sin candidato. Ninguna activaciónMLfútbol.
NBA+2PRE(50),15snapshots(12PRE intactos+3REG20oct)/0outcomes,2123 sin reentrenar;
fases visibles API/UI/reportes. H12laboratorio0alertas/npm10ci/29tests/lint/build,
no publicado por visual bloqueado; producto conserva5altasdev/0prod. SolicitudH4
preparada, no enviada. Propuestas concretas de alcance al cierre, no tareas
manuales de programación ni soportes inexistentes para el propietario.

La tabla siguiente conserva los alcances y cortes anteriores; el corte de uso
local al inicio prevalece para visual/H12/outcomes/H4 actuales.

## Hechos comprobados y límites

| Frente | Cierre acreditado | Pendiente real |
|---|---|---|
| Single-user | Migración con backup, historial deportivo conservado; auth/pagos/tiers retirados de API/UI/BD activos | Revalidar perímetro si cambia topología; visual completo aún no acreditado |
| Entorno y CI | Python3.12 persistente, lock, pruebas PostgreSQL sintéticas, frontend y Compose en CI | Estado de procesos se comprueba al operar; un HTTP200 anterior no demuestra que sigan activos |
| NBA canónico/serving | Selector NBA válido, modelo2123 con30equipos, 73partidos añadidos; reload sin entrenar | No es validación de eficacia; PRE separado de regular |
| Fútbol canónico | 337eventos ESPN vinculados, 200finales, 136programados, 1suspendido; 23.919históricos/apuestas/predicciones conservados, reimportación0/0 | 200finales completados con goles/córners1T/2T explícitos y evidencia separada, rollback/idempotencia/postflight. No imputar desdeFT |
| ML fútbol técnico | Artefacto completo verificable, activación atómica y loader read-only, API/UI sin modelos/MAE/fechas ficticios;771backend/24frontend en ese corte | No hay modelo fútbol activo registrado en el último corte real |
| ML fútbol temporal | Reevaluación tras completar tiempos:618EVAL por familia, política original; frescura reciente recuperada | Ninguna familia apta: cobertura79,13% en las tres y target corners peor. CensoCAL97finales<100mínimo; sin modelos/activación enNeon |
| P&L histórico | Guardas y N/D;114/181binarias NBA no evaluables,67solo aritméticas,8discrepancias deportivas | Propietario confirma que NO existen soportes: no pedirlos ni inventarlos. Exclusión controlada; ROI no certificado |
| Temporalidad histórica NBA | 2.934trazas auditadas:2.136inválidas,476ambiguas,322indeterminadas | 0certificables en ese corte; no convertir histórico en prospectiva |
| Prospectiva NBA | 12capturas Q1raw PRE congeladas antes de inicio, hashes/horas/políticas verificados;0outcomes al último corte | Partidos16/10 23:00Z–17/10 02:30Z, resolución posterior porUUID y fuente independiente; CBScoincide12/12calendarios pero upstream sin acreditar. No repetir capturas |
| KPI/observabilidad | [M04/M05 técnico](../reactivacion_single_user/KPI_PNL_Y_GET_2026-10-16.md): P&L común cross-sport/N/D, grano/cohortes, calibración con serie/n/modelo, sinTTL;78GET revisados y guardas READONLY/errores sanitizados | M12 evaluado:1.303cohortesraw de2–4pares, cero calibradasID/elegibles temporales; confianza/cuotas descriptivas y P&LN/D. Certificación y visual pendientes |
| Mantenimiento | H6/H7 técnico y reproducibilidad/CI cerrados en sus alcances | H12parcial:10→5altasdev/0prod, residuobraces sin parche;0discrepanciasmodo yfavicon reparado. H4ensayo357/357refs y4blobs fuera; remoto aún alcanzable por12heads/13refsPR y cachés, sin purga parcial |

Las cifras de datos/DB corresponden a cortes identificados en sus informes, no a
una consulta permanente. La evaluación temporal usa cinco ligas y desde2023-07;
no se confunde su dataset acotado con el diagnóstico global de persistencia.

## Decisiones del propietario ya resueltas

No hay soportes originales P&L ni tarea humana para recuperarlos. Revisión visual
y diagnóstico del navegador corresponden al agente, con control autorizado.
No existe necesidad concreta pendiente de login/2FA, contratación o gestión
personal GitHub. Un fallo de herramienta no se atribuye a falta de permiso humano.
No hay acciones futuras automáticas ni notificaciones externas configuradas por
estos bloques. El análisis NBA interno mantiene no_picks/no_stake/no_recommendations.

## Histórico preservado, no órdenes vigentes

Los cortes superados y C0–C7/A1–B7/P1–P9 se conservan íntegros en
[estado anterior a la consolidación](../archive/ESTADO_PROYECTO_ANTES_CONSOLIDACION_2026-10-16.md).
Sus cobros, MP, login, premium, dominios y tareas de lanzamiento **no** son requisitos
actuales. Ver ADR-005 histórico y ADR-006 aceptado para artefactos fútbol.

## Regla de cierre

Actualizar estado, changelog, roadmap y evidencia al cerrar cada bloque. No declarar
terminado el conjunto por un cierre técnico ni usar backtesting como promesa futura.
