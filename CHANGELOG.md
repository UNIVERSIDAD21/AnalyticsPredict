# CHANGELOG

## 2026-10-21 — Fecha local y diferencia de puntos NBA

- Alinear la ingesta ESPN con el trigger canónico: `diferencia_puntos` se guarda como magnitud absoluta.
- Guardar `fecha_partido` en la fecha local de Nueva York, igual que el sincronizador del calendario NBA; añadir regresiones de ganador local/visitante y cambio de día UTC.

## 2026-10-21 — Continuación de búsqueda de fuentes gratuitas

- Evaluar metadatos de HF/GitHub, el catálogo oficial de StatsBomb y una página FA Cup permitida por robots. Los candidatos contienen tiros sin córners, marcadores sin estadísticas o solo ligas/upstream sin derechos independientes; ninguno aumenta cobertura residual comprobable. No se descargaron datasets ni se consultó el endpoint `/api/` prohibido.
- Detener búsquedas ante CAPTCHA/desafío humano; sin bypass. Sin DDL/DML ni valores nuevos. Censo de referencia, no recalculado: 4.603/24.593 finales con NULL (26.414 celdas, READ ONLY 01:59:43 UTC). CI `1d18751` 4/4 verde (`39533378261`). Evidencia privada: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_CATALOG_CONTINUATION_20261021T0236Z.json`.

## 2026-10-21 — Prueba autenticada limitada de SportsAPI Pro

- Cuenta Free ya autenticada en Chrome normal; API key guardada en Secret Store del Gateway, acotada a `api.sportsapipro.com` y ausente del repo.
- Validé temporadas, fixtures y estadísticas por periodos con 44 GET en siete competiciones residuales. Seis muestras confirmaron campos y consistencia interna; FA Cup quedó con evidencia parcial de periodos.
- No crucé con Neon ni escribí/importé datos. La respuesta no identifica el upstream; aún no es fuente apta para backfill integral. Evidencia privada `Carpeta de Entregas de Borlty/REGISTRO_SPORTSAPI_PRO_2026-10-20/`.

## 2026-10-21 — Búsqueda pública focal adicional

- Consultar metadatos Hugging Face para `corner football`, `shots soccer` y `football statistics cup`: las tres respuestas HTTP 200 fueron vacías. No es prueba de inexistencia global.
- Inspeccionar el formulario público gratuito de SportsAPI Pro: exige nombre, apellido, email, contraseña y consentimiento a términos; no se transmitieron datos ni se creó cuenta. Sin clave, sus endpoints continúan devolviendo 401.
- Sin consulta ni mutación de Neon; censo de referencia 03:21:18 UTC. Evidencia privada con SHA-256 en `Carpeta de Entregas de Borlty/FUENTES_GRATUITAS_RECHECK_2026-10-20/`.

## 2026-10-21 — Evaluar candidato gratuito SportsAPI Pro

- Revisar páginas públicas de pricing, términos y documentación: plan Free declara 100 requests/día, sin tarjeta, retención de datos obtenidos con clave propia para análisis/modelado y acceso general a competiciones/endpoints.
- La documentación declara profundidad desigual por tier; no garantiza seis métricas por fixture/temporada en las copas/torneos residuales ni define suficientemente el total de disparos. La lista plana de torneos está incompleta; catálogo y planes muestran cifras que requieren validación.
- Consultas sin autenticación a endpoints de torneos, categoría y stats devolvieron 401. El formulario Free requiere nombre, email, contraseña y aceptación expresa de términos; no se envió identidad ni se creó cuenta. Candidato condicionado, no cubre actualmente ningún valor comprobado.
- Evidencia privada con hashes: `Carpeta de Entregas de Borlty/APISPORTSPRO_CANDIDATE_AUDIT_2026-10-20/`. Sin DDL/DML.

## 2026-10-21 — Crosswalk HF y acceso Neon de AnalyticsPredict

- Confirmar que Neon de AnalyticsPredict es accesible por la conexión protegida del proyecto; la integración Neon de OpenClaw apuntaba a otro proyecto y no se usó. No se leyó ni mostró el secreto de conexión.
- Revisar metadatos de permisos dentro de `READ ONLY`; conexión y permisos de trabajo en objetos consultados confirmados, sin afirmar administración irrestricta. Detalle de permisos fuera del repositorio. No se intentaron escrituras.
- Censo `REPEATABLE READ / READ ONLY` (03:21:18 UTC): 24.593 finales FT, 4.603 partidos/26.414 celdas con NULL; 236 vínculos, 1.398 observaciones y 1.396 pares partido-campo. Reparto de gaps por fuente original: 97 ESPN y 4.506 SofaScore.
- Cruzar el snapshot HF declarado CC-BY contra Neon: 800 candidatos exactos. Sus 4.418 campos faltantes son ceros fuente dudosos; 12 partidos tienen 13 conflictos. DataHub no produjo cruces nuevos. Rechazar el lote: 0 valores nuevos, 0 DDL/DML.
- Revisar catálogos gratuitos sin cuentas, claves, emails, compras, trials ni bypass: HF/GitHub sin candidatos nuevos; Kaggle reCAPTCHA detenido; la muestra gratuita de Footiqo es EPL 2025/26 y requiere email/consentimiento de marketing para exportarla. No se obtuvo ni descargó.
- Evidencia privada con SHA-256 verificado: `Carpeta de Entregas de Borlty/HF_CROSSWALK_2026-10-20/`. Sin pruebas ejecutadas; cambios de documentación solamente.

## 2026-10-21 — Revisión amplia de Hugging Face

- Consultar API de datasets con `football match`, `soccer stats` y `football cups`: 17 resultados, 1 y 0. Revisar metadatos/fichas de los candidatos con licencia/cobertura aparente. Ninguno aporta las seis métricas en copas nacionales/UEFA residual bajo permiso abierto: hay duplicados de ligas, resultados sin stats, muestras sintéticas, repos sin procedencia/licencia, o productos pagos. No descargar CSVs.
- CI del commit `0bd75d0` pasó 4/4 (run `39533085455`). La nueva evidencia privada, con manifiesto SHA-256, es `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/HF_BROAD_FOOTBALL_CATALOG_REVIEW_20261021T0229Z.json`. Sin DDL/DML, valores nuevos, cuentas, claves, pagos ni trials; censo de referencia sigue en 4.603/24.593 (26.414 celdas, READ ONLY 01:59:43 UTC).
- Se documentó en el acta privada que `0bd75d0` quedó con correo noreply por una variable del proceso pese al `git -c`; no se reescribirá el commit publicado ni se hará force-push. Los commits siguientes usarán `GIT_AUTHOR_*` y `GIT_COMMITTER_*` explícitos y se verificarán después de crearse.

## 2026-10-21 — Revisión de nuevos catálogos gratuitos

- Verificar CI del commit `90b5973`: 4/4 verde (run `39531836396`). La rama tenía ese commit local sin sincronizar todavía; se incluirá junto con este registro en el siguiente push autorizado.
- Revisar el repo `xgabora/Club-Football-Match-Data`: 238.858 filas anunciadas, 38 códigos de liga/división y seis métricas compatibles, pero no enumera las copas/UEFA residuales; README declara Football-Data.co.uk como upstream y no se acredita una licencia independiente de sus datos. No se descargó el CSV de 45 MB ni se importó.
- Revisar dos resultados GitHub adicionales: el repo UCL con columnas de stats no publica el CSV ni licencia de datos; la guía `withqwerty/football-docs` no es un dataset y no tiene licencia declarada. Ninguno resuelve los gaps.
- La búsqueda OpenClaw sigue sin clave Gemini; Google devolvió página `/sorry` y la lectura de resultados de Brave expiró dos veces, por lo que se detuvo sin bypass. La búsqueda pública de GitHub sí fue accesible. No se cambiaron claves/configuración, no se descargó contenido nuevo y no hubo DDL/DML ni valores aplicados. Censo de referencia READ ONLY: 4.603/24.593 finales con NULL, 26.414 celdas (01:59:43 UTC). Evidencia externa privada: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/GITHUB_FREE_STATS_REPOSITORY_REVIEW_20261021T0224Z.json`.

## 2026-10-21 — Auditoría de muestras y validación de proveedores de fútbol

- Buscar en GitHub HTML datasets abiertos de FA Cup, Norwegian Cup, Taça da Liga y torneos UEFA; no apareció una base histórica elegible. El único resultado UCL era una visualización de la final 2019; el repo MIT `kaany43/Turkish-Super-League-toolkit` se limita a Turquía y no acredita derechos upstream de SofaScore. No se clonó ni ejecutó. Evidencia `GITHUB_HTML_FREE_SOURCE_SEARCH_20261021T0148Z.json`.
- Recontar en Neon bajo transacción REPEATABLE READ/READ ONLY (01:45:25 UTC): 24.593 finales, 4.603 con NULL/26.414 celdas. De los siete grupos internos, 97 gaps corresponden a ESPN_SOCCER (auditoría completa 97/97, sin métricas en summaries) y 4.506 a SOFASCORE. El Kaggle MIT local FA Cup/Coppa Italia (8.856 filas) no cruza ningún canónico por equipos ordenados/aliases exactos y fecha ±1 día. Sin nuevos valores ni DDL/DML.
- Ampliar búsqueda de metadatos gratuita: HF devolvió cuatro listas vacías; Kaggle mostró reCAPTCHA y DuckDuckGo/Mojeek desafíos que se respetaron; Bing no arrojó un candidato exacto útil. El buscador OpenClaw sigue sin clave y no se cambió configuración. Evidencia reproducible `SOURCE_SPLIT_AND_FREE_CROSSWALK_20261021T014525Z.json`; hashes/acta externa.
- Aplicar desde el dataset local gratuito MIT de Kaggle solo seis estadísticas NULL-only a Nancy–Guingamp y Villefranche–PSG: 2 partidos/12 valores. Sus scores de fuente 1–2 y 0–3 coinciden con ESPN independiente aunque los FT canónicos son 1–1 y 0–0; se conservaron sin cambio los marcadores canónicos. Se excluyó Trelissac–Marseille por desacuerdo Kaggle/ESPN. Backup privado, ensayo de rollback, dos vínculos/12 observaciones y postflight independiente READ ONLY. El primer verificador falló después del commit por un NameError; se corrigió y la relectura independiente confirmó valores, procedencia y scores. Censo vigente 01:27:53 UTC: 24.593 finales, 4.603/24.593 partidos con NULL (26.414 celdas), 236 vínculos/1.386 valores/1.398 observaciones. Detectados ejemplos de equipos noruegos bajo ENG_FACUP y portugueses bajo ITA_COPPA; extensión por auditar READ ONLY.
- Ampliar la auditoría con GitHub REST, Harvard Dataverse, Mendeley Data y Zenodo, sin usar resultados de un endpoint bloqueado. El dataset FPL Core Insights publica stats de UCL/UEL/Conference/EFL Cup 2025/26–2026/27, pero 116 filas procesadas dejaron 0 partidos canónicos únicos por identidad/fecha/FT; el upstream FotMob no está autorizado independientemente. Depósitos Harvard CC0 no tienen corners/tiros/SOT o no listan archivos. Mendeley UI arrojó errores de hidratación; GitHub search y Zenodo API respondieron 403 y se detuvieron. Sin datos nuevos. Evidencia privada `CATALOGS_FPL_HARVARD_MENDELEY_GITHUB_20261021.json`; censo READ ONLY 01:59:43 UTC, 4.603/24.593 partidos con algún NULL (26.414 celdas).
- Extender la búsqueda a catálogos públicos DataCite, Figshare, OpenAIRE y Hugging Face. Los tres términos HF guardados devolvieron cero datasets; OpenAIRE arrojó cero para FA Cup y cuatro resultados no pertinentes en `UEFA football`. Figshare identifica un corpus de eventos Wyscout limitado a cinco ligas europeas y torneos de selecciones, no a las copas/torneos de clubes objetivo. DataCite mostró datasets de ligas principales (uno CC BY-NC-ND y otro con salvedad de derechos upstream), no cobertura de copas. `football-data.org` confirma que el plan gratis no incluye estadísticas y que corners/tiros pertenecen al complemento de €15/mes; excluido por la instrucción gratuita. API-Football respondió 403 con challenge y no se reintentó. Sin nuevos datos, cuentas, claves ni DDL/DML. Evidencia externa `PUBLIC_CATALOGS_TARGETED_20261021.json` (SHA-256 `27b5cf336258567b930eaa2acbc53bef328dd9e9009f3648edba8620b4db5334`). CI del commit `83f8a0b` verificado 4/4 verde; censo observado sin recálculo desde 01:59:43 UTC.
- Confirmar con fichas oficiales dos filas que no pertenecen a las competiciones de sus códigos: final de la Norwegian Football Cup Fredrikstad–Molde guardada bajo ENG_FACUP y Sporting–Nacional (Allianz Cup/Taça da Liga) bajo ITA_COPPA. `pais_id` es NULL en sus equipos, así que el alcance de la mezcla sigue desconocido; no se cambió el catálogo. Búsqueda de datasets para estos eventos/categorías en Hugging Face/GitLab/DataCite sin resultados; GitHub y Zenodo devolvieron 403 y se respetaron sin reintento. Ninguna stats nueva; censo por esos códigos no acredita la cobertura de FA Cup/Coppa Italia real. Evidencia `COMPETITION_CROSSWALK_FREE_SOURCE_REVIEW_20261021T0135Z.json`.
- Aplicar la restricción del propietario para el trabajo siguiente: usar únicamente fuentes sin costo, sin tarjeta/renovación y con derechos de almacenamiento/modelado verificados. FootyStats se excluye por créditos de descarga y prohibición de extracción automatizada; StrikerAPI ofrece 500 créditos mensuales gratuitos, pero no cubre las copas nacionales pendientes y sus rondas UEFA con gaps carecen mayormente de boxscores. Sin cuentas, claves, llamadas, pagos ni valores nuevos. El censo continúa en 4.605/24.593 partidos con algún NULL (26.426 celdas); fuente gratuita integral aún no encontrada.
- Consultar catálogos públicos de Kaggle/Hugging Face/Zenodo/OpenFootball por las siete competiciones residuales. Un dataset Kaggle etiquetado CC0 parece incluir stats de copas 2015–2023, pero su ficha declara scraping FBref y aceptación de términos de Sports Reference; no se descargó ni se asumió que la etiqueta del espejo resuelva derechos upstream. Un dataset UCL 2020–2026 con clasificatorias/corners/tiros muestra licencia “Other” y fuente/permiso persistente sin aclarar; tampoco se descargó. Los demás hallazgos son agregados, resultados sin stats, métricas parciales o competiciones fuera del catálogo. No hubo valores nuevos ni cambios en Neon. Evidencia privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.
- Buscar cada competición residual en Kaggle: el dataset Wyscout CC BY 4.0 es solo cinco ligas 2017/18 más dos torneos nacionales, no las copas/UEFA objetivo; el paquete mide 3,23 GB y se descartó sin descarga. Un dataset de estadísticas de jugadores no declara licencia ni cubre métricas de equipo. No se añadieron fuentes ni datos.
- Evaluar in-memory la muestra gratuita de Sports Data Vault (2.721 partidos, 1.828 filas de stats, 12–18 oct 2026): 32 FA Cup clasificatorias, ninguna con estadísticas; no hubo partidos de las otras copas/torneos objetivo. No aporta valores para completar; no se adquirió el archivo completo y la muestra no se persistió ni importó.
- Descartar provisionalmente TheStatsAPI: sus ejemplos públicos contienen Manchester City–Arsenal en FA Cup el 14-sep-2026, contradicho por el calendario oficial de rondas, y reutilizan un mismo ID entre páginas de copas distintas. La retención en DB/modelos no está suficientemente aclarada para la licencia visible. Sin cuenta, API key, trial, compra o contacto.
- Confirmar que API-Football y Sportmonks publican cobertura/estadísticas, pero no permiten verificar desde acceso público la cobertura exacta histórica de cada fixture/campo; se requiere cuenta o clave. Sin credenciales nuevas ni llamadas autenticadas.
- Sin nueva consulta/cambio a Neon: el último censo sigue siendo 4.605/24.593 finales con algún NULL (26.426 celdas, 2026-10-20 23:59 UTC). Sin DDL/DML ni nuevos valores. Evidencia externa privada `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/CATALOG_AUDIT_SUPPLEMENT_20261021.json`, SHA-256 verificado.

## 2026-10-20 — Recuperación multi-fuente parcial y búsqueda ampliada

- Aplicar en Neon valores NULL-only respaldados por ESPN, DataHub PDDL, Kaggle y Hugging Face: 234 vínculos proveedor-partido, 1.374 valores y 1.386 observaciones de procedencia. La tanda DataHub añadió dos LaLiga (12 valores); una excepción de Verona–Roma completó un único corner local `0` corroborado por tres fuentes, conservando el FT canónico 3–0. Ambas pasaron backup privado, ensayo rollback y postflight.
- Actualizar resolver campo-a-campo y el aplicador DataHub para un crosswalk explícito y acotado a `Betis`→Real Betis, `Espanol`→Espanyol y `Sociedad`→Real Sociedad, manteniendo identidad única por competición/fecha/equipos/localía/FT y guardas NULL-only.
- Censo READ ONLY: 24.593 finales FT; 4.605 partidos/26.426 campos aún tienen algún NULL entre corners, disparos y tiros al arco. Los gaps se concentran en copas nacionales/UEFA; no se afirma completitud ni recuperabilidad universal. En Verona–Roma los tiros de DataHub/Kaggle discrepan de ESPN/HF; se preservan valores canónicos y solo se aplica corner 0 explícito, dejando el 3–0 intacto.
- Examinar candidatos CC0/CC-BY y fuentes adicionales; descartar los que no aportan campos, carecen de términos claros o dependen de scraping no autorizado/bloqueado. Confirmar que un mirror HF era duplicado exacto y que datasets recientes carecían de procedencia o cobertura útil. No sortear bloqueos, comprar planes ni usar credenciales no disponibles.
- Cotejar READ ONLY la cobertura UEFA 2025/26 por mes: los gaps Champions/Europa/Conference son clasificatorios de julio/agosto (55/58/181 partidos); ESPN Scoreboard no devuelve eventos para las fechas de muestra y el resumen de la fase principal disponible no deja gaps. Excluir TotalCorner por términos contra extracción automatizada y FCStats por robots.txt/403; persistir evidencia y censo nuevo sin DML.
- Ampliar la revisión de fuentes: catálogo StatsBomb actualizado con Copa del Rey solo 1977/78–1983/84, UCL hasta 2018/19 y sin FA Cup/Coupe de France/Coppa Italia/Conference; sus cruces exactos previos no completan gaps. Stats API documenta stats de partido y declara acuerdo comercial con API-Football, pero el endpoint de cobertura devolvió 401 sin clave y sus términos prohíben un espejo masivo. No se creó cuenta, no se pidió clave ni se consultaron stats protegidas.
- Desglosar Neon en READ ONLY por competencia/temporada/campo (23:59 UTC): 24.593 finales FT, 4.605 partidos y 26.426 celdas nulas, reconciliadas en 53 grupos. Por competencia quedan ENG_FACUP 862, ESP_COPA 338, EUR_CHAMPIONS 336, EUR_CONFERENCE 968, EUR_EUROPA 796, FRA_COUPE 1.106 e ITA_COPPA 199. Sin DML.
- Revisar Footballdata.io: documenta corners/tiros/SOT, pero requiere autenticación, no acredita cobertura pública por competencia-temporada y sus términos reservan posible permiso escrito/enterprise para almacenamiento prolongado, replicación masiva o warehouse. No se creó cuenta, no se consultaron estadísticas ni se modificó Neon. El mirror GitHub jokecamp/FootballData mezcla upstreams; su licencia MIT no acredita derechos sobre las estadísticas originales.
- Actualizar la continuidad con el nuevo lead y la evidencia externa privada `FOOTBALLDATA_IO_PUBLIC_CONTRACT_20261020/`; la búsqueda de fuentes elegibles sigue abierta.
- Revisar dos repositorios más anunciados en GitHub: uno declara ligas principales 2008–2016 y otro Premier League 2010–2021; no tienen licencia reconocida y no cubren los gaps de copas/UEFA. No descargar CSV/base ni incorporar valores.
- Buscar repositorios por seis competiciones objetivo: sin resultados candidatos. Para Europa League se respetó un HTTP 403 de rate limit sin reintento; las búsquedas no se presentan como prueba de inexistencia.
- Verificar Footiqo: exports manuales oficiales admiten uso privado no comercial en DB/modelos, pero scraping y descargas automatizadas están prohibidas. La navegación lista tres torneos UEFA, no las copas nacionales. Preparar guía/matriz agregada de 21 temporadas UEFA (2.100 partidos/11.874 gaps potenciales); no se obtuvo ningún archivo ni se modificó Neon.
- Revisar la exportación manual de Footiqo solo como posible vía gratuita UEFA: no muestra copas nacionales, falta acreditar cobertura por fixture/temporada y requiere un correo/consentimiento para la muestra. No se pidió ni descargó archivo; queda sin validar, no como solución integral.
- Auditar Sportmonks como lead histórico: su cobertura gratuita no incluye los torneos objetivo y las temporadas/historiales restantes no se pueden comprobar desde las páginas abiertas. Excluido por no satisfacer el filtro gratuito actual; no se creó cuenta, no se pidió clave ni se hizo llamada.
- Buscar catálogos directos de Hugging Face y GitHub para copas/UEFA: los resultados nuevos fueron datasets de top-5 ya completos, video/robótica, UCL limitado o apps/análisis aislados, sin dataset histórico elegible nuevo. La API de Kaggle respondió con página de verificación de navegador; se detuvo sin cookies ni bypass. Evidencia privada `SPORTMONKS_SOURCE_AUDIT_2026-10-20/`.
- Evaluar StatPal/SoccerDataAPI y Goalserve desde páginas públicas: ambos anuncian históricos y estadísticas (corners/tiros), pero no se confirmó cobertura de fixtures/temporadas objetivo ni derechos de almacenamiento suficientes. StatPal no expuso términos accesibles en la ruta publicada; Goalserve ofrece trial por contacto y no muestra condiciones/precio aplicables. No se creó cuenta, contactó, trial ni API call. Detener consultas a Scorebing y documentación de API-Football al recibir HTTP403, sin evasión.
- Excluir un repo reciente `vsntll/xValue` que publicita estadísticas de copas mediante FotMob: GitHub no declara licencia y FotMob prohíbe servicios automatizados y uso sistemático/regular; su `robots.txt` desautoriza `/api/*` para agentes generales. No se clonó ni descargó repo/datos, no se ejecutaron scripts ni se solicitaron páginas/API de partidos.
- Ampliar búsqueda de datasets en GitHub, Hugging Face y Zenodo. `xgabora/Club-Football-Match-Data` publica una licencia MIT del repositorio, pero su README atribuye las estadísticas a Football-Data.co.uk y describe solo ligas/divisiones; no acredita derechos independientes del upstream ni cobertura de las copas residuales. Otros resultados tenían alcance top-5, solo resultados/horas de gol, cobertura limitada, licencia no comercial/sin derivados o procedencia/licencia no verificable. No se descargaron nuevos CSV, no hubo escrituras en Neon; evidencia privada `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/`.
- Evaluar in-memory una muestra HF gratuita de 20 partidos UEFA: dos cruces canónicos únicos aparecieron y ambos ya tenían las seis métricas; tres muestras no existen en Neon en ±1 día. La oferta ampliada es de pago, no cubre copas nacionales ni la mayoría de clasificatorias y queda excluida por instrucción del propietario; `Goal_Attempts` no tiene equivalencia documentada a tiros totales. No se aplicó la muestra ni se adquirió producto alguno.
- Reconciliar tablas de lotes con contadores actuales de Neon en consulta READ ONLY; registrar el censo de cierre. Alinear constraints de migraciones hermanas para que el orden alfabético de aplicación no reduzca la allowlist de fuentes y sanitizar errores operativos sin imprimir detalles del driver/DSN.
- Actualizar fuente de verdad, estado, roadmap y acta externa con límites, procedencia y continuidad. Sin cambios en apuestas/modelos ni ingestas programadas.


## 2026-10-19 — Desarrollo ML fútbol con forma causal y nueva cohorte futura

- Implementar selección temporal de Ridge identidad/forma/híbrido, ataque/defensa5/20, descanso/contexto de liga y refit final explícito. No consumir outcomes del partido ni de eventos simultáneos; los históricos de desarrollo no certifican el modelo final.
- Evaluar1.193eventos,1.157pares goles/disparos y96,98%cobertura con mejora frente a baseline de liga; córners619pares/51,89%, no apto. Mantener V1/V2/V3 sin modificaciones.
- Congelar251partidos20oct–1dicUTC con251predicciones de goles/251disparos/223córners+28abstenciones; techo córners88,84%<90. Artefactos completos con coeficientes/features/estado/hash y CLI externa READONLY, sin sobrescribir.
- Mantener probabilidadesN/D,0MLfútbol activos y promoción/calibración pendientes. Sin DML/ingesta/cron/serving/NBA/bitácora;887backend/0fallos/0skips y dos deprecaciones heredadas. Evidencia externa `ML_FUTBOL_FORMA_TEMPORAL_V4_2026-10-19`.

## 2026-10-19 — Consulta y guardado neutral de partidos de fútbol

- Desde Fútbol, guardar el partido seleccionado para volver a revisarlo en una lista separada de Bitácora; reabrirlo por UUID aunque quede fuera del calendario próximo y retirarlo mediante archivo lógico.
- Persistirlo con estado propio y sin mercado/pick/probabilidad/stake ni DDL; excluirlo del listado, resumen, auditoría, métricas de calidad y backfill de apuestas.
- Mantener visible que fútbol no tiene un modelo ML activo. Verificar con seis pruebas backend dirigidas/simuladas, build/lint frontend; ninguna escritura de prueba a la base real.

## 2026-10-18 — Recuperación de datos enero–octubre y finales pendientes

- Contrastar 2.928 finales de 12 competiciones fútbol, NBA y Euroliga; aplicar 273 altas/108 actualizaciones fútbol, 18 altas/6 fases NBA y 183 altas Euro, con respaldo privado, ensayo/rollback y postflight independiente.
- Ampliar capturas/vínculos a copas/europeas; reconocer AET/PEN, validar mitades/ET/tandas y agregado sin inventar periodos ni alterar la semántica del ganador. Conciliar históricos solo por manifiesto explícito y huella previa; preservar estadísticas y afiliaciones.
- Corregir play-in ESPN tipo 5 a POST, permitir estado de ingesta NBA dentro de una transacción externa y añadir adaptador oficial Euro con cuartos/OT/FT e identidad verificados.
- Conservar apuestas, modelos y prospectiva: once huellas intactas; sin reentrenar/activar/resolver, P&L N/D y eficacia NO CERTIFICADA. 875 backend/36 frontend aprobadas, lint/build/audit producción 0.

## 2026-10-16 — Uso local visual, H12 y contratos de análisis

- Migrar Tailwind4/PostCSS oficial con lock y audit0, conservar tema/utilidades y validar vistas reales y móvil emulado.854backend/36frontend/lint/build.
- Reparar selección/identidad/paginación/NULL de fútbol y registro con savepoint/enum canónico; bitácora con identidad canónica sin reescribir histórico y fechas sin desfase.
- Sincronizar navegación por deporte, cabecera/título y textos single-user; análisisNBA interno sin datos de ejemplo, con fase/corte temporal tantoSQLcomo fallback y errores sanitizados.
- Diferenciar outcomes registrados de independientes enEstado:15capturas/9resultadosPRE/0independientes, aplicación previa ensayada/idempotente y huellas intactas. Sin reentrenar ni calibrar; diagnósticoPRE no certifica eficacia.
- Actualizar H4: ticket#4868445cerrado por proveedor sin coordinación de refs/cachés; sin purga parcial/forcepush. Ver ARRANQUE_VISUAL_Y_USO_LOCAL_2026-10-16.

## 2026-10-16 — Pasada integral: datos verificados y cohortes futuras separadas

- Aplicar426finales adicionales con goles por mitades/FT/tiros y163programados de noviembre sin marcadores; backup privado, rollback, idempotencia y postflight.38colisiones retenidas y358rechazos de córners por periodo, sin forzar datos.
- Reconciliar el postflight genérico de completitud con triggerFT idéntico al previo; conservar incidencia y regresión, sin DML correctivo. V1reevaluada con política original, ninguna familia apta.
- CongelarV2 de laboratorio para199futuros:163predicciones/36abstenciones porfamilia, techo81,91%<90%. VarianteV3declarada antes de outcomes conserva mínimos y falla CALefectivo88/78; no activar ni ocultar versiones.
- Incorporar2finalesPRE NBA sin actualizar histórico y congelar3REG20oct;12PRE originales intactos,15hashes/relojes verificados,0outcomes, modelo2123 sin reentrenar.
- Completar migraciónH12 aislada (audit0/npm10ci/tests/lint/build), no publicada por bloqueo visual. Preparar solicitudGitHub y propuesta de allowlistlocal sin contacto ni cambios globales.848backend/29frontend; eficacia NO CERTIFICADA.

## 2026-10-16 — Preparación estacional fútbol y conservación de fases NBA

- Añadir preparación y evaluación posterior de candidatos Ridge aislados: política futura, CAL por partidos previos, mínimos conservados, abstenciones, integridad y salidas externas no sobrescribibles. No activar modelos ni fabricar probabilidades/calibradores.
- Mostrar datos y seguimiento NBA por PRE/REG/POST; reporte de forma reciente con selector NBA válido y filtro por fase. Conservar pretemporada sin mezclar su eficacia con regular.
- Preservar afiliación actual de clubes al ingerir histórico y contar evidencia correctamente bajo psycopg pipeline, con regresiones PostgreSQL.
- Documentar 464 finales revisados, 38 colisiones retenidas y candidatura de 426 a aplicación controlada. Migración H12 preparada externamente sin publicar mientras falte visual; expediente Git sin contacto remoto. Ver el documento del bloque para límites y cierre efectivo.

## 2026-10-16 — Ejecución de los siete frentes y límites medidos

- Completar200finales con goles/córners por mitades, evidencia separada, rollback e idempotencia. Postflight detectó el flag derivado del trigger: reconciliado con backup/huellas sin DML adicional y prueba SQL incorporada; guardia de prórroga protege FT.
- Reevaluar fútbol con política original:618EVAL/familia, ninguna apta por cobertura79,13% y targetcorners. Censo15lotesCAL arroja97finales<100mínimo, sin ingerirlos ni aflojar gates.
- Ejecutar M12 descriptivo:1.303cohortesraw n2–4, cero cadenas certificables/calibradasID. Contrastar CBS12/12calendarios sin atribuir independencia primaria.
- Ensayar H4privado357/357refs,4blobs fuera; remoto sin purga parcial. Confirmar bloqueo visual y residuoH12dev5altas/prod0. No cerrar prospectiva futura, deuda ni certificación por estos avances.

## 2026-10-16 — Córners por mitades acreditados

- Extender el contrato ESPN con cronología completa, límites UTC, identidad/periodo y reconciliación FT. Aplicación atómica de ocho campos; evidencia separada y controles de idempotencia/contradicciones. No acredita aptitud ni independencia NBA.

## 2026-10-16 — preparación de goles fútbol por mitades

- Parser y CLI de tiempos explícitos ESPN, identidad/UTC/FT y dos periodos exactos, sin imputar a partir de FT; cohorte200/200 comprobada. Observaciones separadas, plan de solo lectura por defecto y aplicación atómica/idempotente sin sobrescribir contradicciones. Migración y pruebas SQL preparadas; aplicación/evaluación posterior se acreditan por separado.

## 2026-10-16 — KPI/P&L común y auditoría GET

- Política monetaria compartida NBA/fútbol/combinadas: agregados N/D sin soportes/unidad, n/exclusiones/motivos; individuales y filas preservados. Cohorte de resumen/listado fútbol igual antes de paginar, fechas y columnas canónicas, sinTTL. Combinadas no se multiplican por selecciones.
- GET/HEAD protegidos con contexto y PostgreSQL READ ONLY, conexiones reutilizadas/concurrentes aisladas de POST. Serializador fútbol sin escrituras; fallos reales no se publican como éxitos vacíos. Errores sanitizados/trace_id/contadores, sin trazas DEBUG ni errores técnicos persistidos expuestos.
- Auditoría78GET con grafo transitivo y contraste ASGI/huellas; corregidas ruta estática ocultada porUUID, UUID del driver, límite Query de resumen y columnas legacy de madurez sin cambiar sus gates. Sin DDL/DML productivo, ingestas, capturas ni modelos. Ver `docs/reactivacion_single_user/KPI_PNL_Y_GET_2026-10-16.md`.

## 2026-10-16 — compatibilidad de instalación npm del runner

- Override explícito selector-parser7.1.6 para npm10/11: el primer pushH12 falló instalaciónfrontend/Compose por interpretación del override condicionado. npm10.8.2ci/27tests/lint/build pasan con el mismo lock sin reintroducir parser vulnerable; no se omiten gates.

## 2026-10-16 — H12 parcial y dependencias de desarrollo

- Vite7.3.7/pluginReact5.2 compatibles y Node mínimo declarado; overrides picomatch2.3.2/selector-parser7.1.6. Auditoríadev10→5altas,prod0, sin suprimir advisories ni forzarTailwind4. Residuo braces<=3.0.3sin parche publicado;H12abierto.
- npmci/27tests/lint/build verdes y CSS Tailwind idéntico byte a byte. Cero discrepancias de modo/sin chmod; favicon vacío sustituido por SVG válido con MIME coherente. Serviciosloopback reanudados sin autoentrenar; visual sigue sin acreditarse por denegación de herramienta, no de propietario.

## 2026-10-16 — coherencia de KPI de calibración

- Resumen/curva/API/UI con serie raw o calibrada homogénea, n/exclusiones/modelo/periodo coherentes. Default raw, ECE/MCE nullable sin pares, muestra pequeña visible y sin falsa excelencia/drift. Sharpness como varianza y base_rate de la misma cohorte; mejora no atribuida entre muestras distintas.
- Cachés300s retiradas de esos dos GET, cálculo UTC bajo demanda sin precálculos; errores503 sanitizados, no éxito/n0.794backend/27frontend/lint/build;4GETASGIreales200 enREADONLY y7huellas intactas. P&L/otrosKPI/caches/GETintegral siguen abiertos; NO CERTIFICADO.

## 2026-10-16 — evaluación temporal fútbol y continuidad consolidada

- Evaluación Ridge read-only con protocolo predeclarado TRAIN/CAL/EVAL, alpha soloCAL, baseline e IC pareado por partido; fechas/IDs/equipos desconocidos y ventanas sinCAL explícitos. CV temporal no divide perspectivas ni presenta ajuste como validación cuando faltan folds.
- Resultado:581EVALcorners/goles y618disparos; MAE1,396/0,665/2,679 frente a1,426/0,686/2,907. Ninguna familia pasa todos los gates; no se guardaron ni activaron modelos fútbol enNeon. Backtesting no acredita disponibilidad histórica ni eficacia futura.
- Estado/roadmap/deuda consolidados, versiones anteriores archivadas íntegras. Confirmación del propietario: soportesP&L no existen, exclusiones/ROI N/D sin tarea documental humana; no hay login/compra/GitHub personal identificados como requisitos.

## 2026-10-15 — ciclo ML fútbol verificable

- Artefacto JSON Ridge completo por familia, contrato de features/targets, dataset efectivo y SHA-256; registro canónico sin DDL, lote atómico y activación validada antes de desactivar. Recarga SQL read-only sin entrenar, NPZ sin pickle y rechazo de versiones incompletas/ambiguas.
- Selector válido/final por target, cutoffs UTC, NULL sin imputación, coherencia deportiva y mínimos por equipo; n de partidos separado de perspectivas. CLI diagnóstico por defecto y publicación/activación explícitas, con recarga verificadora y selección de familias.
- API/UI dejan de fabricar modelos, MAE, estado activo o próximo entrenamiento. N/D se conserva; ajuste in-sample no recibe etiqueta de validación. Artefacto raw sin reutilizar calibrador de otra versión.
- Diagnóstico Neon solo lectura: corners14.136/goles10.716 hasta marzo; disparos14.379 hasta12/10. Cero versiones fútbol/entrenamiento/activación, nueve huellas históricas y12capturasNBA/0outcomes intactos.771backend/24frontend/lint/build; cinco GETAPI+Estadofront200. ADR-006 aceptado; rendimiento NO CERTIFICADO.

## 2026-10-15 — operación local y cadena prospectiva NBA

- Estado read-only API/UI, frescura por dominio, artefacto y último job; fallo503/ausenciaN/D, nunca ceros fabricados. Rutina manual explícita sin cron/notificaciones ni entrenamiento en GET.
- Cadena Q1 Ridge raw en tablas paralelas: evento/features/coeficientes/hash/dataset/modelo, reloj BD anterior al inicio, snapshot inmutable y resolución final idempotente. Sin calibrador ficticio, picks, stakes, cuotas ni recomendaciones. Tras CI2b142e0 4/4/ensayo: instalada en Neon,12capturas reales PRE futuras, reimportación0 y nueve huellas históricas intactas;0outcomes aún.
- Fútbol2378058 CI4/4, ensayo real aislado y Neon aplicado:337 eventos,200 finales,136 programados,1suspendido; histórico23.919 y apuestas/predicciones intactos; reimportación0/0. API devuelve49 próximos.
- Auditoría ML fútbol: sin modelo activo registrado y sin carga persistida implementada; gestor legacy incompatible con esquema actual. No se reentrenó/activó nada. FT no imputa tiempos.
- Pruebas de este lote:751 backend sintéticas sin fallos/omitidas,21frontend/lint/build verdes. Smoke6GET API+6rutas frontend200; visual pendiente por política del navegador. NBA CDN alternativo403, no eludido. Rendimiento NO CERTIFICADO.

## 2026-10-15 — vínculo canónico ESPN fútbol

- Adaptador con manifiesto de identidades explícitas, sin fuzzy matching, y tablas separadas de IDs/procedencia ESPN. Alta controlada de temporada/clubes, anti-duplicados entre fuentes y DML atómico/idempotente; revisiones antiguas no sobrescriben datos nuevos ni degradan finales.
- Manifiesto revisado contra catálogo y rosters ESPN2026: 96 clubes, dos altas nuevas (Hull/Coventry), cinco temporadas2026–27. Dry-run 337 eventos: 200 finales, 136 programados y un abandonado→suspendido, sin goles imputados. Cobertura FT no inventa métricas de primer/segundo tiempo.
- Suite local sintética de este lote: 740 passed, sin fallos/omitidas. Aplicación canónica aún pendiente de CI/ensayo/postflight.

## 2026-10-15 — preparación para uso: entorno y dominio NBA

- Checklist de ejecución con resultados y pendientes en `docs/reactivacion_single_user/CHECKLIST_PREPARACION_USO_2026-10-15.md`. Entorno Python 3.12 persistente con lock; frontend local Node 24: lint, 19 tests y build verdes, además de CI Node 20.
- Entrenamiento/backtest/conteos comparten filtro NBA explícito, `valido=true`, marcador positivo y cuartos no negativos/coherentes. El hash incluye dominio, política e identidad completa de entradas. El serving formato 2 rechaza artefactos legacy sin dominio/calidad acreditados, incluido el mixto de 58 entidades.
- Ingesta NBA rechaza el lote entero ante fallos de parseo y escribe atómicamente; permite exclusión manual por ID con motivo (exhibición Portland–London Lions 401914130). Dry-run: 40 finales candidatos/0 fallos/1 exclusión, aún sin DML.
- El CLI de análisis permite salida externa; sus tests dejan de regenerar reportes históricos rastreados. El arranque frontend instala con `npm ci` y exige puerto estricto.
- Ajuste de compatibilidad: `hash_datos` conserva el contrato PostgreSQL `varchar(32)` mediante SHA-256 truncado a 128 bits, con algoritmo explícito en metadata. La primera operación detectó la longitud incompatible antes de registrar versión/publicar artefacto; los 73 partidos ingresados no se repiten.

## 2026-10-15 — capturas ESPN Soccer independientes

- Se completa el WIP de capturas por liga/mes, con observación UTC, hashes scoreboard/boxscore, ingesta atómica idempotente y revisiones conservadas. GET read-only del último lote; `SIN_CAPTURA`, `NO_DATA` y almacén no disponible diferenciados. No modifica el catálogo canónico ni resuelve apuestas.
- Nueva captura delimitada: 337 eventos de cinco ligas en septiembre/octubre, 200 finales con goles/corners/tiros completos. Suite backend sintética: 733 passed, cero fallos/omitidas. Ver `docs/reactivacion_single_user/CAPTURAS_ESPN_SOCCER_2026-10-15.md`; recertificación y mapeo canónico pendientes.
- CI de código `5647c79` 4/4 verde; tablas/capturas aplicadas a Neon tras ensayo con rollback y preflight. Postflight independiente: 10 lotes/337 eventos/200 finales, reimportación 0/0, once huellas canónicas intactas. Sin inicio de servicios ni enlace al modelo.

## 2026-10-06 — resúmenes de fútbol y vistas ROI legacy

- Los resúmenes API de apuestas/sistema fútbol calculan ROI registrado sobre stake resuelto únicamente y devuelven `null` si falta cualquier ganancia resuelta; el adaptador cliente conserva N/D. Pruebas dirigidas backend/frontend y build cubren el contrato sin DML.
- Se identificaron tres vistas SQL legacy con ROI sin gate. La migración conservadora publica `NULL` manteniendo columnas/tipos; se ensayó en PostgreSQL desechable antes de aplicarse. No equivale a vista KPI certificada.
- Tras CI 4/4 de `361e493`, la migración se aplicó a Neon con respaldo privado y postflight read-only: 182/1/7 filas, contratos, owner y ACL intactos; ROI no nulo = 0 en las tres vistas. El GET `/api/bitacora/estadisticas` también deja de publicar ROI bruto; conserva ganancia como importe registrado.
- El CLI descriptivo `validar_baselines_nba.py` mantiene n, win rate y montos registrados, pero publica ROI N/D hasta certificar procedencia; sus SELECT ahora corren bajo transacción read-only. La prueba de integración usa datos sintéticos.

## 2026-10-06 — semántica analítica single-user vigente

- El catálogo KPI refleja el gate actual 114/181/67 del P&L. El mapa semántico y el inventario de vistas distinguen implementaciones reales de propuestas históricas; N/D, fuente, grano, exclusiones y límites prospectivos quedan explícitos. No se creó una vista física nueva ni se declaró rendimiento certificado.

## 2026-10-06 — probe controlado de ESPN Soccer

- Se añadió auditor read-only de calendario/resultado mensual ESPN Soccer con kickoff UTC, marcador final explícito y corners/tiros solo con dos equipos completos. 403 o contrato roto detienen el lote sin retries ni escritura; 200 vacío produce `NO_DATA` solo para mes/liga consultados.
- Probe La Liga: 36 finales en marzo 2026 (dos boxscores completos en muestra) y 36 programados en octubre 2026, cero finales al corte. Quedan pendientes mapeo de equipos/IDs, cobertura por liga, ingesta a Neon y outcomes prospectivos.

## 2026-10-06 — mantenimiento H12 y scripts legacy

- Se retiró del Makefile el target de notificaciones B4, cuyo script ya no existe en la herramienta single-user. El resto de targets conserva scripts presentes.
- El script RC-A comercial que referenciaba un test de auth retirado se archivó sin borrar su contenido; la CI vigente sustituye ese gate.
- Tres capturas JSON de 2026-02-22 de cero bytes salieron del índice Git y permanecen en copias locales/historia. `reports/README.md` documenta que son capturas fallidas, no datos vacíos válidos; no se imputaron valores.
- La CI fija `ubuntu-24.04` y usa acciones oficiales `checkout/setup-python/setup-node@v6` para evitar el salto implícito de imagen y la deprecación de runtime Node 20 de las acciones previas. Mantiene Node 20 para la app hasta validar una migración de dependencias separada.

## 2026-10-06 — ROI fútbol registrado sin cero ficticio

- El endpoint de rendimiento deja ROI, ganancia y win rate en `null` si falta denominador o importe completo; la serie temporal deja ROI/ganancia en `null` hasta tener muestra y ganancias observadas. No se reescribió ninguna apuesta.
- El cliente convierte el porcentaje de ROI de la API a razón una sola vez y muestra N/D si falta dato; los resúmenes globales/por categoría no convierten mercados incompletos en 0 %. El ROI que sí existe se rotula **registrado**, no certificado.

## 2026-10-06 — reconciliación oficial de marcadores NBA y Euroliga

- Neon: 81 finales NBA y un final Euroliga reprogramado recuperaron marcador/cuartos oficiales; 67 pospuestos NBA y 82 filas Euroliga sin final en su registro 0–0 quedaron `valido=false`, preservados. Respaldo, ensayos transaccionales, postflight read-only y rollback ensayado fuera del repositorio. Cinco apuestas y 66 vínculos de predicción no cambiaron.
- El P&L excluye resultados que contradicen marcador/línea/lado: 111/181 binarias no evaluables, ocho discrepancias deportivas, ROI no certificado. PR #177 y CI 4/4 verde en PR y rama canónica. Ver `docs/reactivacion_single_user/RECONCILIACION_MARCADORES_BALONCESTO_2026-10-06.md`.

## 2026-10-06 — apuestas sin evento vinculado y alias ESPN legacy

- Auditoría read-only detectó 40 apuestas sin `partido_id` (39 binarias y una anulada); tres binarias y la anulada eran aritméticamente coherentes, pero carecían de un evento que permita cotejar el outcome. El gate de bitácora/auditoría las excluye: **114/181 binarias** (115/182 filas totales) no evaluables y **67 binarias** solo aritméticamente coherentes. Ocho resultados son incompatibles con marcador.
- Neon normalizó `source/source_game_id` en 219 NBA desde `fuente_datos=ESPN` y `espn_game_id`: 219 IDs únicos, sin colisiones ni cambios de marcador. Backup/postflight SHA-256 y rollback ensayado fuera del repo. ROI sigue NO CERTIFICADO.

## 2026-10-06 — alcance NBA y estados externos de partidos 0–0

- El auditor y scorecard NBA delimitan la competición: 10.286 partidos NBA y 148 NBA 0–0, frente a 12.775/231 de baloncesto agregado en informes previos. Contraste read-only de 148 IDs ESPN: 67 pospuestos y 81 finalizados con marcador positivo ausente en Neon. La ingesta detecta ID ESPN legacy aunque `source` sea nulo: dry-run de abril pasó de 39 inserciones duplicadas previstas a 0. Los 83 0–0 Euroliga siguen sin verificación externa. No se alteraron filas históricas ni el dictamen NO CERTIFICADO.

## 2026-10-06 — guard de 0–0 en combinadas legacy

- La ruta de resolución de selecciones de combinadas conserva pendiente un evento NBA con ambos totales 0, sin calcular resultado ni actualizar la selección. Neon read-only mostró 0 selecciones combinadas enlazadas a esos partidos en este corte; el cambio evita nuevas resoluciones espurias.

## 2026-10-06 — vista agregada NBA sin outcomes 0–0

- Se aplicó migración transaccional e idempotente de `vista_resumen_calibracion` para no computar pares de partidos 0–0. Postflight Neon: 2.582→2.558 pares; 12 columnas, owner/grants, vista base y 2.934 predicciones históricas intactos. Rollback preparado y ensayo en PostgreSQL efímero; no se usó en Neon.
- Lecturas de reporte de backtest y drift calculan con `persistir=False`; no generan precálculos implícitos. `metricas_calibracion` y `alertas_calibracion` tenían cero filas en el corte read-only. H9 científico y bloque E siguen abiertos por verificación independiente de outcomes y prospectiva.

## 2026-10-06 — propagación de outcomes NBA 0–0 a KPI y backtest

- Salud, calidad por mercado y drift distinguen outcome registrado de evaluable; historial muestra `NO_EVALUABLE` y excluye esos casos de ganadas/perdidas. El gate de calidad NBA, recalibración, resumen/curva/reporte de backtest y estadísticas de resolución ya no tratan 0–0 como resultado válido.
- Reporte de backtest deja de consultar alias de equipos ausentes en la vista H9 productiva y conserva la fila dudosa rotulada, sin transformarla en PUSH. Cotejo read-only con Neon: 24 exclusiones en salud/historial/backtest; 2.558 outcomes NBA evaluables. Certificación y vista SQL agregada histórica siguen pendientes.

## 2026-10-06 — exclusión analítica parcial de resultados NBA 0–0

- Auditor read-only conserva 2.934 predicciones, excluye 24 outcomes no acreditados y deja 2.558 pares raw descriptivos. Cálculo/curva de calibración enmascaran esos resultados, muestran su conteo y GET recalcula sin precálculo legacy ni UPSERT.
- Bitácora conserva cinco apuestas vinculadas a 0–0 pero las excluye del gate ROI; 107/181 binarias quedan no evaluables (103 previas y cuatro adicionales). CLI P&L deja 74 binarias solo aritméticamente coherentes, todavía no certificadas. Salud/calidad/drift y otros consumidores siguen pendientes de auditoría.

## 2026-10-06 — diagnóstico seguro de fuentes deportivas

- Dry-run NBA exige transacción read-only, detiene HTTP 401/403 sin reintentos y rechaza marcadores 0–0 o cuartos/OT no acreditados; ESPN devolvió 8 partidos ya presentes en la ventana 1–6 de octubre. El sincronizador fútbol abandona impersonación/recuperación de 403, incorpora dry-run read-only, distingue fuente caída de cero eventos, usa UTC, preserva goles 0 y no marca estadísticas parciales como completas. Sofascore respondió 403, sin ingesta.

## 2026-10-06 — datos históricos dudosos y guard de resolución

- Corte read-only clasifica 219 NBA sin alias `source` (todos con ID ESPN), 231 marcadores 0–0 (81 en ambos grupos), 25 fútbol finalizados sin goles, 24 predicciones NBA resueltas y 5 apuestas enlazadas a 0–0. Los resolvedores NBA bloquean nuevas resoluciones desde 0–0; históricos intactos y KPIs aún no recertificados.

## 2026-10-06 — clasificación temporal histórica NBA

- Auditor read-only clasifica 2.934 predicciones: 2.136 con cutoff posterior al día UTC de generación, 476 ambiguas y 322 no determinables. Ninguna tiene evidencia completa para certificación temporal; no se altera el histórico ni se atribuye ausencia de leakage. Suite backend local PostgreSQL desechable: 661 passed, 0 failed, 0 skipped.

## 2026-10-06 — clasificación P&L NBA y ROI condicionado
- Auditoría read-only y reproducible de 182 apuestas/181 resultados binarios: 102 importes incompatibles con fórmula neta y una fila adicional con cuota del lado discrepante; 103 no evaluables para ROI, 78 binarias aritméticamente conciliables pero no certificadas. Valores históricos intactos.
- API de resumen y métricas devuelve ROI `null` en segmentos con P&L NBA no evaluable, expone conteos y conserva ganancia como importe registrado. Dashboard/Bitácora/Métricas muestran N/D y exclusiones. GET de bitácora deja de escribir contadores locales de contrato.
- Suite backend Python 3.12/PostgreSQL sintético 657 passed, 0 failed, 0 skipped; frontend 16 tests, lint y build verdes. Dictamen analítico sigue **NO CERTIFICADO** por procedencia y temporalidad.

## 2026-10-06 — serving NBA sin entrenamiento implícito
- Startup/reload y GET de salud/modelo cargan solo artefacto versionado fuera del repositorio; entrenamiento, registro y recarga son operaciones explícitas. GET de explicación deja de escribir telemetría en BD.
- Suite local Python 3.12/PG sintético 651 passed, 0 failed, 0 skipped; CI de PR #167 (`37534587737`) y rama (`37534829259`) 4/4 verdes.
- Un entrenamiento explícito publicó artefacto privado (modo 0600) del modelo ID 2122; tras reload del backend canónico siguieron 2.122 versiones en Neon. Dataset último partido 2026-05-05; modelo **NO CERTIFICADO**.

## 2026-10-06 — vistas H9 con procedencia en Neon
- Neon auditada read-only: la vista NBA tiene 42 columnas y una vista resumen dependiente que también usaba probabilidad calibrada sin procedencia. Definiciones originales de ambas vistas guardadas para rollback externo.
- Migración H9 ampliada para exigir calibrador resoluble del mismo mercado y probabilidad válida; prueba PostgreSQL efímera cubre nueve casos, contratos y rollback. Suite backend local: 646 passed, 0 failed, 0 skipped. CI de PR #167: 4/4 verde.
- DDL transaccional aplicado a Neon bajo orden del Jefe de continuar el plan; contrato, owner/grants y 2.934 filas históricas conservados. Cinco mercados NBA suman 2.582 pares raw y cero calibrados con ID. La semántica técnica de vistas quedó alineada, sin certificación científica o prospectiva.

## 2026-10-06 — H9 temporal y suite sin omisiones
- Nueve tests omitidos pasan a ejecución en PostgreSQL sintético; calibración fútbol excluye backtest/sintéticos, fuga temporal y outcomes no disponibles. Diagnóstico usa conexión read-only; `GOLES_FT` mostró 0 pares elegibles en Neon, sin guardar calibrador.
- B16/B17/B20A/B20B exigen ID para usar probabilidad calibrada. Migración compatible de vista NBA preparada y ensayada, **no aplicada a Neon**. Suite local Python 3.12: 646 passed, 0 failed, 0 skipped; frontend 16 tests, lint/build verdes. CI `b8a6d74`: 4/4 jobs (run `37518301706`). H9 y dictamen analítico siguen abiertos.

## 2026-10-06 — consumidores de vista NBA con procedencia
- Curvas, calculador y reporte de backtest no usan `p_efectiva`/`p_calibrada` legacy sin `calibrador_id`; parámetro opcional de versión tipado para PostgreSQL. La vista productiva no se alteró.
- Cotejo Neon read-only: 0 pares calibrados con ID en ambos deportes; 81 pares raw fútbol entre 24 mercados. Suite local PostgreSQL sintético: 629 passed, 0 failed, 9 skipped. H9 y dictamen analítico siguen abiertos.
- CI del código `50a372e`: 4/4 jobs verdes, incluidos PostgreSQL efímero y Compose.

## 2026-10-06 — consumidores H9 sin atribución falsa de calibración
- Gates y métricas operativas NBA/fútbol, explicación, auditoría de decisiones y reportes fútbol usan raw si falta ID de calibrador; N/D sustituye métricas ausentes y el ECE retrospectivo bajo no declara aptitud de producción.
- Suite global con PostgreSQL sintético: 627 passed, 0 failed, 9 skipped; frontend 16 tests, lint y build verdes. H9 sigue abierto por vista/consumidores históricos y cotejo con datos actuales.

## 2026-10-06 — suite global sobre PostgreSQL desechable
- Runner local/CI crea una base aleatoria en PostgreSQL local, carga un esquema sintético sin datos productivos, ejecuta la suite backend y elimina la base. Rechaza hosts remotos y bases administradoras distintas de `postgres`.
- Nueve tests NBA con mocks aíslan gates de BD ajenos a su objetivo. Gate local: 621 passed, 0 failed, 9 skipped; frontend: 16 tests, lint, build/typecheck y audit de producción pasaron. Los skips y la validación CI se registran en `docs/reactivacion_single_user/AUDITORIA_SUITE_GLOBAL_2026-10-06.md`.

## 2026-10-06 — procedencia de calibración fútbol
- El gestor conserva UUID del artefacto cargado y solo publica probabilidad calibrada tras transformación identificada; ausencia, fallo o salida inválida quedan `null`.
- Inferencia ML, persistencia, endpoint de métricas y UI separan raw/calibrada; ajuste de muestra y mezcla heurística no se atribuyen a un calibrador. El histórico 567/567 sin ID no se modifica ni certifica; ver `docs/reactivacion_single_user/CALIBRACION_FUTBOL_PROCEDENCIA_2026-10-06.md`.

## 2026-10-06 — avance H9 sin certificación
- Fórmulas binarias canónicas y `null` sin muestra para Brier, Log Loss y ECE en calculadores principales; raw/calibrada separados, comparación sobre muestra pareada y alertas de cobertura.
- Auditoría agregada exige `calibrador_id` para medir serie calibrada; scorecard fútbol deja de publicar tasa de resolución artificial y claim temporal no comprobado. H9 permanece abierto; ver `docs/reactivacion_single_user/H9_METRICAS_PROBABILISTICAS_2026-10-06.md`.

## 2026-10-06 — CI efímera y corte analítico sin certificación
- Lock frontend regenerado con npm 10 para compatibilidad con Node 20/npm 10 de Docker y CI; validado con instalación limpia, lint, 11 tests, auditoría de producción y build bajo esa misma versión.
- Ingesta ESPN por fecha individual con deduplicación por clave natural legacy; 8 partidos NBA de pretemporada ingresados en Neon tras dry-run, integridad e idempotencia verificadas. No certifica outcomes ni modelos.
- Lecturas GET de bitácora desacopladas de auto-resolución y DDL. Esquemas comerciales sin consumidores retirados; reglas y scorecard local de calidad, catálogo semántico KPI v0, inventario legacy/rot y preflight H4 documentados. H4 no se declara purgado.
- Suite backend global segura: 578 passed, 19 failed dependientes de PostgreSQL de pruebas no disponible en host, 11 skipped. Gates dirigidos, frontend lint/11 tests/build y auditoría de dependencias de producción en verde; 10 alertas de dependencias dev siguen abiertas.
- Lock de 51 dependencias Python 3.12; CI de la rama con contratos, unitarias analíticas, frontend, migración PostgreSQL efímera y smoke Docker Compose privado (4/4 jobs verdes en run 37481234870).
- `.dockerignore` excluye envs, DB locales y caches de las imágenes. La migración se probó con dos identidades sintéticas, conservación de histórico y rechazo/rollback de ganador incorrecto.
- Corte read-only previo a la ingesta NBA/fútbol/confidence/odds/calidad: **NO CERTIFICADO**. En ese corte no había partidos finalizados recientes; luego se ingresaron 8 NBA de pretemporada. 102/181 P&L NBA no cumplen fórmula decimal y 2.136/2.934 cutoffs NBA son posteriores al día de generación. Detalle y límites en `docs/reactivacion_single_user/RECERTIFICACION_ANALITICA_2026-10-06.md`.
- Smoke visual de rutas clave sin login con datos no vacíos; ROI/ganancia históricos rotulados como registrados/no certificados en dashboard, bitácora y métricas. Lectura read-only reveló intento de auto-resolución/escritura desde GET; no se completó ninguna escritura de esa prueba.
- ADR-005 y el índice comercial de ejecución inmediata se marcaron `SUPERADO`; el roadmap single-user es la referencia operativa vigente.

## 2026-10-05 — contratos, métricas y limpieza single-user
- Bitácora frontend consume v2 explícito y valida envelopes; un error o payload desconocido no se interpreta como lista vacía. Analizadas usa `FINALIZADA` y total global independiente de la página.
- Hit rate 1X2 conserva escala porcentual; sin muestra se publica `null`. Calibración fútbol calcula Brier, ECE y Log Loss desde outcomes válidos o publica `null`, sin multiplicadores proxy.
- CI incorpora pruebas dirigidas backend y tests frontend. Bases SQLite comerciales y telemetría runtime salen del índice Git sin borrar copias locales; scripts de backup/restore SQLite comercial y variables obsoletas del ejemplo de entorno se retiran.
- Ver `docs/reactivacion_single_user/REPORTE_ELIMINACION_CAPA_COMERCIAL.md` para evidencia y límites. Integración con BD efímera y recertificación analítica siguen pendientes.
- Entorno local reanudado en loopback; `/salud`, OpenAPI y raíz frontend respondieron HTTP 200. El arranque entrenó el modelo habitual, sin que ello certifique rendimiento o datos.
- Compose local opcional deja de depender de SMTP/MailHog y credenciales comerciales; su smoke consulta solo salud/OpenAPI. Validación estática, sin Docker ni despliegue.

## 2026-10-05 — inicio de reactivación single-user
- Aprobada dirección de producto privado personal; C0–C7 queda como historia, no objetivo vigente.
- Creado snapshot de recuperación e inventario de auth, pagos, usuarios, rutas, datos y frontend; arquitectura y plan de migración documentados sin tocar BD.
- Endurecidos defaults locales de desarrollo/Compose a loopback y desactivada la liberación automática de puertos en `dev.sh`.
- La retirada de auth/pagos/tiers y la migración de datos siguen pendientes de perímetro privado comprobado y ensayo aislado; no se declaran resueltos H1–H3.
- Inventario posterior de Neon en transacción de solo lectura: 4 usuarios, 3 IDs con apuestas y FKs de bitácora; la propiedad histórica continúa sin clasificar. Ver `docs/reactivacion_single_user/INVENTARIO_DATOS_SINGLE_USER_2026-10-05.md`.

## 2026-04-03
- Bloque 20B fútbol (auditoría y priorización de la familia de GOLES):
  - Nuevo pipeline reproducible: `backend/scripts/auditoria_goles_b20b.py` para mercados `GOLES_FT`, `GOLES_1T`, `GOLES_2T`, `GOLES_LOCAL_FT`, `GOLES_VISITANTE_FT`.
  - Se extiende marco operativo (scorecard básico, readiness, freshness y ranking de rescatabilidad) a la familia GOLES.
  - Reportes generados:
    - `docs/reportes/BLOQUE_20B_AUDITORIA_GOLES_FAMILIA.json`
    - `docs/reportes/BLOQUE_20B_AUDITORIA_GOLES_FAMILIA.md`
  - Resultado de corrida: 5/5 mercados en `NO_LISTO` y rescatabilidad `BAJA`; no se detectan finalizados/resolubles en ventana activa para abrir rescate inmediato.
  - Recomendación formal: `no_abrir_rescate_goles_todavia`.
  - Comparación estratégica GOLES vs CORNERS: empate en cuello principal de calendario/masa (finalizados_30d=0 en ambos frentes).
- Bloque 20A fútbol (expansión del marco de madurez a familia corners restante):
  - Nuevo pipeline de expansión/auditoría por mercado: `backend/scripts/expansion_corners_b20a.py`.
  - Mercados core evaluados: `CORNERS_FT`, `CORNERS_2T`, `CORNERS_VISITANTE_2T`; opcionales auditados: `CORNERS_VISITANTE_1T`, `CORNERS_LOCAL_FT`.
  - Extensión práctica del framework (scorecard+readiness+freshness) a esa familia en un reporte único reproducible.
  - Ranking de rescatabilidad generado y causas explícitas de bloqueo (actualmente todos en `NO_LISTO`, rescatabilidad `BAJA` por ausencia de finalizados/resolubles en ventana).
  - Rescate técnico focalizado condicional integrado en pipeline; en esta corrida no aplicó (sin casos finalizados con datos pendientes de resolver).
  - Artefactos:
    - `docs/reportes/BLOQUE_20A_EXPANSION_CORNERS_FAMILIA.json`
    - `docs/reportes/BLOQUE_20A_EXPANSION_CORNERS_FAMILIA.md`
- Bloque 19.7 fútbol (automatización diaria consolidada con alertas y disparo controlado):
  - Entrypoint único diario: `backend/scripts/automation_diaria_corners_b19_7.py`.
  - Integración operacional de `freshness (B19.6) + tracking (B19) + readiness gate (B18)` en snapshot consolidado diario.
  - Motor de alertas por cambios relevantes en `backend/motor_futbol/automation_diaria.py`:
    - primer `VENCIDO`,
    - subida de `AMARILLO`,
    - aumento de masa resolutiva,
    - cambio de readiness,
    - habilitación de gate de reevaluación,
    - habilitación de gate B20.
  - Disparo controlado a B20: solo se registra habilitación; **no** ejecución automática (`NO_EJECUTAR_B20_AUTOMATICO`).
  - Reportes y estado diario:
    - `docs/reportes/BLOQUE_19_7_AUTOMATION_DIARIA_CORNERS.json`
    - `docs/reportes/BLOQUE_19_7_AUTOMATION_DIARIA_CORNERS.md`
    - `docs/reportes/BLOQUE_19_7_AUTOMATION_STATE.json`
  - Runbook/cron template: `docs/reportes/BLOQUE_19_7_RUNBOOK_AUTOMATION_DIARIA.md`.
- Bloque 19.6 fútbol (vigilancia automática de PROGRAMADO vencido y stale data):
  - Política SLA formal para `PROGRAMADO` en mercados foco (`CORNERS_1T`, `CORNERS_LOCAL_1T`) en `backend/config/futbol_sla_programado_vencido_b19_6.json`.
  - Motor de clasificación de frescura implementado: `backend/motor_futbol/freshness_programado.py`.
  - Pipeline de vigilancia reproducible: `backend/scripts/vigilancia_programado_vencido_b19_6.py`.
  - Reportes generados:
    - `docs/reportes/BLOQUE_19_6_VIGILANCIA_PROGRAMADO_VENCIDO.json`
    - `docs/reportes/BLOQUE_19_6_VIGILANCIA_PROGRAMADO_VENCIDO.md`
  - Snapshot actual por mercado foco: 16 `PROGRAMADO` (8 SANO, 8 AMARILLO, 0 VENCIDO).
  - Señal operativa actual: `calendario_real_sin_vencidos` (no abrir bloque de ingestión todavía).
- Bloque 19.5 fútbol (auditoría E2E post-partido y conversión a outcomes binarios en mercados prioritarios):
  - Nueva auditoría extremo a extremo de cadena `emisión -> estado partido -> datos corners 1T/local 1T -> resolución -> persistencia outcome` para `CORNERS_1T` y `CORNERS_LOCAL_1T`.
  - Script reproducible: `backend/scripts/auditoria_resolucion_corners_b19_5.py` (incluye opción `--apply-backfill` cuando detecta resolubles atascados).
  - Reportes generados:
    - `docs/reportes/BLOQUE_19_5_AUDITORIA_RESOLUCION_CORNERS.json`
    - `docs/reportes/BLOQUE_19_5_AUDITORIA_RESOLUCION_CORNERS.md`
  - Evidencia de ventanas 7/14/30: hubo emisiones nuevas pero `0` partidos finalizados y `0` pendientes resolubles con datos; no se detectó pipeline roto en la conversión para estos dos mercados.
  - Diagnóstico formal: cuello principal actual = calendario real (`PROGRAMADO`), con gate B20 correctamente bloqueado.
  - Backfill focalizado ejecutable/condicional: al no existir pendientes resolubles detectados, no hubo rescates en esta corrida.
- Bloque 19 fútbol (plan operativo de acumulación de masa resolutiva para corners prioritarios):
  - Nuevo motor de tracking longitudinal: `backend/motor_futbol/readiness_tracking.py`.
  - Nuevo pipeline reproducible de progreso por ventanas 7/14/30 días: `backend/scripts/plan_acumulacion_masa_b19.py`.
  - Reportes de progreso y readiness delta por mercado foco:
    - `docs/reportes/BLOQUE_19_PLAN_ACUMULACION_MASA_CORNERS.json`
    - `docs/reportes/BLOQUE_19_PLAN_ACUMULACION_MASA_CORNERS.md`
  - El tracker mide emitidos/resueltos/cerrados nuevos, pendientes estimados por calendario, tasa de resolución, delta de gap vs baseline B18 y proyección de horizonte para cerrar gaps.
  - Gate formal de disparo a B20 incorporado: solo habilita re-scorecard seria cuando **ambos** mercados (`CORNERS_1T`, `CORNERS_LOCAL_1T`) tienen `gate_reevaluacion_seria_habilitado=true` en la misma corrida.
  - Snapshot actual: ambos mercados siguen NO_LISTO; con ritmo semanal observado de resolución (=0), el horizonte estimado para reevaluación seria queda indeterminado (N/D) hasta registrar resueltos binarios nuevos.
- Bloque 18 fútbol (umbral duro de masa resolutiva + gate de reevaluación para corners prioritarios):
  - Nueva política explícita para `CORNERS_1T` y `CORNERS_LOCAL_1T`: `backend/config/futbol_readiness_gate_corners_b18.json`.
  - Umbrales duros formalizados: mínimos de masa binaria para reevaluación/salida de bloqueo/candidatura a validación, máximo de pendientes tolerable, mínimo de coverage y estabilidad temporal mínima.
  - Nuevo motor de readiness: `backend/motor_futbol/readiness_gate.py` con cálculo de `readiness_status`, gaps y motivos no-silent.
  - Integración de gate en re-scorecard: `backend/scripts/re_scorecard_corners_b17.py` ahora degrada a `BLOQUEADO` con motivo `gate_readiness_no_habilitado` cuando no cumple readiness.
  - Integración en monitoreo: `backend/scripts/monitoreo_autodemotion_futbol.py` evalúa readiness en mercados foco y evita ascensos silenciosos con evidencia insuficiente.
  - Nuevo reporte operativo de readiness: `backend/scripts/gate_readiness_corners_b18.py` + artefactos `docs/reportes/BLOQUE_18_READINESS_GATE_CORNERS.{json,md}`.
  - Estado actual cuantitativo en ambos mercados foco: `NO_LISTO` (masa 4/28, gap 26 para reevaluación seria, gate de reevaluación BLOQUEADO).
- Bloque 17 fútbol (reejecución con evidencia real, 20:58Z):
  - Reejecución del script `backend/scripts/re_scorecard_corners_b17.py` usando entorno `.venv`.
  - Confirmación cuantitativa reproducible: `CORNERS_1T` y `CORNERS_LOCAL_1T` permanecen `BLOQUEADO` (`NO_APTO`) por `volumen_o_resolucion_critica`.
  - Sin mejora de masa binaria (`4 -> 4`), con mejora operativa limitada (`pendientes 24 -> 16`).
  - Evidencia de corrida y pruebas: `docs/reportes/BLOQUE_17_REEJECUCION_EVIDENCIA_2026-04-03T20-58-38Z.md`.
- Bloque 17 fútbol (re-scorecard comparativa y reevaluación de estado):
  - Re-scorecard focalizado ejecutado para `CORNERS_1T` y `CORNERS_LOCAL_1T` con comparación estricta antes vs después.
  - Resultado cuantitativo: mejora operativa parcial (`pendientes -8` por mercado), pero sin aumento de masa binaria resuelta (`4 -> 4`), por lo que ambos mercados se mantienen `BLOQUEADO`.
  - Se documenta explícitamente no sobreinterpretar Brier/LogLoss/ECE con n binario pequeño.
  - Decisión de ruta: **Ruta 2** (seguir acumulando masa resolutiva en estos dos mercados antes de intentar promoción).
  - Artefactos generados:
    - `docs/reportes/BLOQUE_17_RESCORECARD_CORNERS_COMPARATIVA.json`
    - `docs/reportes/BLOQUE_17_RESCORECARD_CORNERS_COMPARATIVA.md`
- Bloque 16 fútbol (rescate técnico focalizado de mercados prioritarios):
  - Foco estricto en `CORNERS_1T` y `CORNERS_LOCAL_1T` (sin expansión a 24 mercados).
  - Corrección operativa en resolución: predicciones de partidos `CANCELADO/POSPUESTO/SUSPENDIDO/ABANDONADO` pasan a cierre `VOID` (`resuelto=true`) para evitar pendientes estructurales.
  - Grilla de líneas focalizada y defendible:
    - `CORNERS_1T` -> `[4.5, 5.0, 5.5]`
    - `CORNERS_LOCAL_1T` -> `[2.5, 3.5, 4.5, 5.0]`
  - Script de rescate/auditoría focalizada: `backend/scripts/rescate_corners_prioritarios_b16.py`.
  - Evidencia antes/después y diagnóstico específico por mercado en:
    - `docs/reportes/BLOQUE_16_RESCATE_CORNERS_PRIORITARIOS.json`
    - `docs/reportes/BLOQUE_16_RESCATE_TECNICO_CORNERS_PRIORITARIOS.md`
  - Pruebas reales añadidas para resolución/coverage en mercados foco.
- Bloque 15 fútbol (auditoría de causa raíz de bloqueo total por mercado):
  - Se implementa auditoría causal reproducible `backend/scripts/auditoria_causal_bloqueo_futbol.py` usando evidencia de bloques 10, 12 y 13.
  - Se genera matriz causal por cada uno de los 24 mercados con severidad y evidencia cuantitativa.
  - Se consolidan causas raíz por grupo (datos/ETL, resolución/outcomes, coverage, calibración, modelo/features, monitoreo/gates).
  - Se publica ranking de rescate y foco priorizado de 2-3 mercados para siguiente fase.
  - Reportes generados:
    - `docs/reportes/BLOQUE_15_AUDITORIA_CAUSAL_BLOQUEO_FUTBOL.json`
    - `docs/reportes/BLOQUE_15_AUDITORIA_CAUSAL_BLOQUEO_FUTBOL.md`
- Bloque 14 fútbol (cierre de beta, promoción parcial y limpieza narrativa):
  - Se alinea narrativa oficial de producto/documentación con evidencia real de bloques 10–13 (sin sobrepromoción).
  - `docs/FUENTE_DE_VERDAD_ACTUAL.md` actualizado: fútbol queda definido como beta global con madurez diferenciada por mercado, promoción parcial y reversible.
  - Se documenta cierre honesto de etapa: en snapshot actual no hay mercados promocionables (0/24), por lo que no procede salida beta global.
  - Se incorpora reporte final de cierre con tabla de mercados por estado, riesgos residuales y criterio de revisión futura.
  - Se ajusta copy visible para evitar lectura de “todo fútbol beta indiferenciado” o “fútbol terminado”.
- Bloque 13 fútbol (shadow/paper mode operativo y validación prolongada):
  - Se formaliza `PAPER_SHADOW` como modo operativo por mercado no promocionable en trazabilidad de análisis (`objetivo.trazabilidad.modo_operativo`).
  - Nuevo endpoint `GET /api/futbol/metricas/shadow-operativo` con métricas longitudinales por mercado (emitidos, resolubles, resueltos, cobertura de líneas, fallback, brier, estado operativo vigente).
  - Nuevo pipeline de reporte por ventanas semanal/quincenal/mensual: `backend/scripts/reporte_shadow_mode_futbol.py`.
  - Evidencia generada en `docs/reportes/BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json` y documento técnico `BLOQUE_13_SHADOW_MODE_PAPER_MODE_OPERATIVO.md`.
  - Frontend endurecido para visibilizar explícitamente modo PAPER/SHADOW cuando mercado no es promocionable.
- Bloque 12 fútbol (monitoreo continuo y auto-demotion por mercado):
  - Se implementa regla de auto-demotion en `motor_futbol/madurez_beta.py`: los mercados pueden bajar automáticamente de estado cuando empeoran; no hay auto-promoción.
  - Nuevo pipeline `backend/scripts/monitoreo_autodemotion_futbol.py` para vigilancia periódica por mercado (Brier/LogLoss/coverage/fallback/resolución) y decisión de degradación con motivos trazables.
  - Nuevo endpoint `GET /api/futbol/metricas/estado-operativo-mercados` para exponer estado vigente por mercado desde tabla canónica cuando exista.
  - Evidencia reproducible de monitoreo en `docs/reportes/BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json`.
  - Reporte técnico del bloque: `docs/reportes/BLOQUE_12_MONITOREO_CONTINUO_AUTODEMOTION.md`.
- Bloque 11 fútbol (política formal de salida beta y promoción parcial por mercado):
  - Se formaliza política canónica en `backend/config/futbol_politica_promocion.json` con estados `BLOQUEADO|LABORATORIO|VALIDACION|PROMOCIONABLE`, significados operativos y reglas de transición cuantitativas.
  - Nuevo endpoint `GET /api/futbol/metricas/politica-promocion` para exponer política auditable en runtime.
  - `backend/api/rutas_analisis_futbol.py` incorpora estado operativo por mercado en `objetivo.trazabilidad` (`estado_operativo_mercado`, `motivos_estado_operativo`) para cerrar backend→contrato→UI.
  - Frontend (`ResultadoAnalisis`) muestra explícitamente estado operativo del mercado y mantiene gate beta estricto cuando hay condiciones críticas.
  - Se agrega propuesta de persistencia canónica por mercado en SQL (`backend/scripts/sql/bloque_11/01_tabla_estado_operativo_mercado.sql`).
  - Reporte de bloque: `docs/reportes/BLOQUE_11_POLITICA_FORMAL_SALIDA_BETA_PROMOCION_PARCIAL.md`.
- Bloque 10 fútbol (walk-forward + scorecard de promoción por mercado):
  - Nuevo pipeline reproducible `backend/scripts/walkforward_scorecard_futbol.py` con ventanas explícitas train/cal/eval sin leakage.
  - Scorecard exportable por mercado generado en JSON/CSV (`docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.*`).
  - Clasificación operativa formal de salida (`BLOQUEADO|LABORATORIO|VALIDACION|PROMOCIONABLE`) mapeada desde reglas cuantitativas en `motor_futbol/madurez_beta.py`.
  - Prueba de integridad temporal de ventanas walk-forward: `backend/tests/test_futbol_walkforward_scorecard.py`.
  - Reporte ejecutivo de bloque: `docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_PROMOCION_FUTBOL.md`.
- Bloque 9 fútbol (gate cuantitativo de salida beta):
  - Se implementa clasificación formal de madurez por mercado (`NO_APTO|EXPERIMENTAL|VALIDACION|PROMOCIONABLE`) en `backend/motor_futbol/madurez_beta.py`.
  - Nuevo endpoint `GET /api/futbol/metricas/madurez-beta` con matriz de madurez, bloqueados, candidatos promoción y criterios reproducibles.
  - Nuevo script batch `backend/scripts/reporte_madurez_futbol_beta.py` para generar reporte automático (`docs/reportes/BLOQUE_9_MADUREZ_FUTBOL_AUTO.json`).
  - Endurecimiento de frontend gate en `ResultadoAnalisis`: modo validación beta explícito y supresión de bloques contextuales/razones cuando hay degradación crítica de coverage.
  - Adaptador fútbol propaga advertencias severas de coverage y mantiene mensajería honesta de recomendación.
  - Pruebas nuevas y reforzadas: `backend/tests/test_futbol_madurez_beta.py` + regresión frontend.
- Bloque 8 fútbol (auditoría correctiva PSG vs Toulouse `CORNERS_LOCAL_1T`):
  - Se elimina contradicción H2H visible (muestra superior vs tarjeta): el adaptador reconcilia `contexto.h2h` con la muestra canónica reportada por backend (`objetivo.calidadDatos.muestras.h2h`).
  - Récord H2H ahora explícito como `G-E-P` para que cierre con el total de partidos mostrado.
  - Se corrige contradicción lógica de recomendación: sin recomendación formal del mercado objetivo ya no aparece texto de "coincide con la recomendación del sistema".
  - Panel Base vs Ajustada solo se renderiza cuando hay ajuste contextual real; si no, se muestra aviso explícito de no ajuste efectivo.
  - Se elevan advertencias de severidad cuando el mercado objetivo queda fuera de cobertura (`estado_mercados_vacio`, `mercado_objetivo_fuera_estado_mercados`).
  - Se profesionaliza texto de razones (unidad específica de mercado, sin `unid` genérico).
  - Regresión agregada en `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts` para el caso canónico.
  - Reporte del bloque: `docs/reportes/BLOQUE_8_AUDITORIA_CORRECTIVA_PSG_TFC_CORNERS_LOCAL_1T.md`.
- Bloque 7 fútbol (coherencia H2H/historial/UI sin rehacer base):
  - `backend/api/rutas_analisis_futbol.py`: H2H e historial del análisis quedan restringidos por `competicion_id` + gobernanza temporal existente (temporadas/fecha mínima), evitando contaminación de contexto cross-competición.
  - `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.ts`: el contexto renderizado deja de usar goles como proxy genérico y pasa a resolver métrica real por mercado objetivo (goles/corners/disparos, incluyendo 1T/2T cuando aplica).
  - Se alinea perspectiva del partido (equipo/rival/total) y línea visible con la métrica correcta del mercado activo.
  - Pruebas nuevas:
    - `backend/tests/test_futbol_contexto_competicion.py`
    - `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
  - Reporte técnico: `docs/reportes/BLOQUE_7_COHERENCIA_H2H_HISTORIAL_UI.md`.
- Bloque 6 fútbol (capa de decisión canónica y trazable):
  - `backend/api/rutas_analisis_futbol.py`: se formaliza base matemática de decisión con `calibracion_aplicada` explícita, `edge_raw` canónico y recomputación canónica de `edge_real/score/sizing` en arbitraje ENSEMBLE para evitar mezcla opaca de transformaciones.
  - Fórmulas operativas explícitas:
    - `edge_raw = p_raw - (1/cuota_lado)` cuando aplica.
    - `edge_real = p_decision - p_mkt_fair`, con `p_decision = p_calibrada` solo si `calibracion_aplicada=true`, de lo contrario `p_raw`.
  - `backend/api/schemas_futbol.py`: se extiende contrato con `calibracion_aplicada` y `edge_raw` en recomendación/objetivo sin romper render existente.
  - `frontend/src/servicios/futbol/analisis.ts` y `frontend/src/tipos/futbol.ts`: parser/tipos alineados para nuevos campos (`calibracionAplicada`, `edgeRaw`).
  - Pruebas reforzadas en `backend/tests/test_futbol_p51_p61_unittest.py` para fórmulas canónicas y guardas de calibración efectiva.
  - Reporte técnico del bloque: `docs/reportes/BLOQUE_6_CAPA_DECISION_FUTBOL.md`.
- Bloque 5 NBA (blindaje ETL de temporada en pipeline real):
  - Ruta validada y documentada del pipeline real en `docs/reportes/BLOQUE_5_PIPELINE_TEMPORADAS.md`.
  - `backend/scripts/scraper_equipos_recientes.py` ahora resuelve `temporada_id` por evento con trazabilidad explícita:
    - inferencia por fecha (`Oct-Dic => año+1`, `Ene-Jun => año`),
    - fallback controlado a creación/lookup de temporada,
    - advertencias estructuradas cuando `season_api` difiere de fecha o cuando no se logra resolver temporada.
  - Se evita persistir partidos con `temporada_id` vacío; esos casos quedan omitidos y auditables.
  - Pruebas automáticas nuevas: `backend/tests/test_temporadas_scraper_equipos_recientes.py` (asignación correcta, bordes, temporadas cruzadas y fallback controlado).
- Bloque fútbol (gobernanza temporal real en análisis):
  - `backend/api/schemas_futbol.py`: se formaliza contrato de request con `temporadas` y `fecha_minima` (mutuamente excluyentes).
  - `backend/api/rutas_analisis_futbol.py`:
    - se implementa resolución canónica de filtro temporal (`temporadas` explícitas → default activa+anterior → fallback `fecha_minima` trazable);
    - `_obtener_partidos_equipo`, `_obtener_partidos_liga`, `_obtener_partidos_h2h` ahora soportan filtro por `temporada_id` o fallback por fecha mínima;
    - se agrega ponderación por recencia en medias/desviaciones (sin romper contrato de respuesta);
    - se expone trazabilidad temporal en `objetivo.trazabilidad.temporal` con estrategia, temporadas resueltas, fecha mínima efectiva y tamaños de muestra.
  - `backend/tests/test_futbol_filtro_temporal.py`: pruebas unitarias reales para contrato temporal, resolución de filtros, SQL de consulta y ponderación de recencia.
  - `frontend/src/tipos/futbol.ts` y `frontend/src/servicios/futbol/analisis.ts`: contrato cliente alineado para enviar `temporadas`/`fecha_minima`.

## 2026-03-31
- Bloque 2 (arquitectura de bitácora única con transición controlada):
  - Se define documento canónico de transición: `docs/arquitectura/ARQUITECTURA_BITACORA_UNICA_TRANSICION.md` (fuente de verdad de lectura, contrato final, convivencia legacy y plan de migración).
  - `backend/api/rutas_bitacora.py`:
    - `/api/bitacora/unificada` deja de depender de `vista_bitacora_unificada` y pasa a consolidar en una sola lectura `apuestas` + `apuestas_futbol` + `apuestas_combinadas`.
    - Se agregan filtros canónicos: `deporte`, `mercado`, `confianza`, además de resultado/tipo/fecha/búsqueda.
    - Se extiende el contrato de registro con campo `deporte`.
    - `/api/bitacora/resumen` ahora incluye agregado global + por deporte + por mercado, incluyendo fútbol en el consolidado.
  - Frontend bitácora unificada:
    - `PaginaBitacora`, `useBitacora`, `FiltrosApuestas`, `ListaBitacoraUnificada`, `tipos/combinadas` actualizados para soportar filtro y visualización por deporte.
- Bitácora global compartida entre cuentas (ajuste solicitado):
  - `backend/api/rutas_bitacora.py`: endpoints de lectura agregada (`/api/bitacora/unificada`, `/api/bitacora/resumen`, métricas) pasan a visibilidad global (sin filtro por `usuario_id`).
  - Impacto: cualquier usuario autenticado verá el mismo pool de apuestas y resúmenes consolidados.

- Persistencia reforzada de registro/login en tabla de negocio `usuarios`:
  - `backend/servicios/auth_store.py` ahora crea/mantiene espejo en `usuarios` al registrar usuario (email, nombre, password_hash, timestamps, rol, activo).
  - En PostgreSQL se crea `usuarios` (si no existe) con esquema de negocio; en SQLite se crea tabla equivalente de compatibilidad.
  - `actualizar_password` sincroniza hash tanto en `auth_users` como en `usuarios`.
  - `obtener_usuario_por_email` en PostgreSQL incluye fallback de compatibilidad: si existe en `usuarios` pero no en `auth_users`, crea registro sombra en `auth_users` para no romper flujo auth actual.

- Reescritura completa del módulo de autenticación (Auth v2 canónico):
  - `backend/api/rutas_auth.py` reimplementado de cero para registro/login/refresh/logout/me/forgot/reset/accept-legal con flujo directo, validación explícita y trazas de diagnóstico de store activo.
  - Se mantiene contrato de respuesta `v2` (`{ ok, data, meta }`) para compatibilidad con frontend actual.
  - Normalización estricta de email (`strip().lower()`) en registro/login/recuperación para evitar inconsistencias.

- Fix de compatibilidad SQLite en suscripciones (error `no such column: updated_at`):
  - `backend/servicios/pagos_store.py` agrega migración liviana al iniciar `SQLitePagosStore` para crear columnas faltantes en instalaciones antiguas:
    - `subscriptions.source_payment_id`
    - `subscriptions.updated_at`
  - Con esto `/api/pagos/suscripcion/mia` deja de romper con 500 en bases SQLite pre-migración.

- Diagnóstico reforzado de autenticación para detectar desalineación de stores:
  - `backend/api/rutas_auth.py` ahora registra en logs de `register/login`:
    - email recibido,
    - store activo (`SQLiteAuthStore`/`PostgresAuthStore`),
    - `db_path` cuando aplica.
  - Objetivo: identificar en runtime si el alta/login está entrando a una base distinta de la que se inspecciona manualmente.

- Hardening de consistencia de stores (auth/pagos/onboarding):
  - `backend/servicios/pagos_store.py`: si `PAGOS_STORE_DRIVER` no está definido, ahora hereda `AUTH_STORE_DRIVER`; para sqlite, si `PAGOS_DB_PATH` no está definido y sí existe `AUTH_DB_PATH`, reutiliza su directorio para ubicar `pagos.db` y evitar desalineación de datos entre autenticación y suscripción.
  - `backend/servicios/onboarding_store.py`: si `ONBOARDING_STORE_DRIVER` no está definido, ahora hereda `AUTH_STORE_DRIVER`; para sqlite, si `ONBOARDING_DB_PATH` no está definido y sí existe `AUTH_DB_PATH`, reutiliza su directorio para `onboarding.db`.
  - Objetivo: prevenir escenarios donde login funciona contra un store y pagos/onboarding consultan otro distinto (síntoma típico: usuarios/suscripciones "desaparecidas").

- Corrección de sesión/401 en dashboard y servicios protegidos:
  - `frontend/src/servicios/api.ts`: cuando falla refresh/token inválido, ahora se invalida sesión de forma explícita y se emite evento global `auth:session-invalidated` (también limpia `usuarioId`) para evitar ciclos de llamadas 401.
  - `frontend/src/contextos/AuthContext.tsx`: se suscribe al evento de sesión inválida, limpia estado auth y fuerza salida de rutas protegidas de manera consistente.

- Bloque 4 (limpieza y cierre de deuda UX/arquitectura):
  - Eliminados artefactos de UI legacy que duplicaban herramientas compartidas:
    - `frontend/src/componentes/paginas/BitacoraFutbol.tsx`
    - `frontend/src/componentes/paginas/DashboardFutbol.tsx`
    - `frontend/src/hooks/useBitacoraFutbol.ts`
  - Se retiran exportaciones legacy asociadas en:
    - `frontend/src/componentes/paginas/index.ts`
    - `frontend/src/hooks/index.ts`
    - `frontend/src/hooks/useFutbol.ts`
  - Se mantiene compatibilidad de rutas antiguas por redirección (`/futbol/bitacora` → `/bitacora`, `/futbol/dashboard` → `/dashboard`) para transición sin ruptura.

- Bloque 3 (dashboard único de plataforma):
  - `frontend/src/componentes/paginas/PaginaDashboardUsuario.tsx` incorpora segmentación por deporte usando bitácora única (`por_deporte`) para consolidar seguimiento en una sola pantalla personal.
  - Dashboard mantiene una sola ruta canónica (`/dashboard`) y centraliza lectura de estado cross-deporte sin mezclar flujos de análisis.
  - `frontend/src/componentes/paginas/index.ts`: se depreca export público de `DashboardFutbol` para reforzar dashboard único.

- Bloque 1 (unificación de plataforma en navegación):
  - `frontend/src/App.tsx`: rutas legacy de UX `/futbol/bitacora` y `/futbol/dashboard` ahora redirigen a `/bitacora` y `/dashboard`.
  - `frontend/src/componentes/organismos/Encabezado.tsx`: navegación de Bitácora y Dashboard pasa a rutas globales (sin bifurcar por deporte).
  - `frontend/src/componentes/paginas/PaginaFutbol.tsx`: acceso de dashboard apunta a `/dashboard` global.

- Correcciones operativas post-validación en entorno local:
  - `frontend/src/componentes/paginas/PaginaDashboardUsuario.tsx`: carga resiliente con `Promise.allSettled` para evitar caída completa del dashboard cuando falla el endpoint de plan/suscripción; ante fallo parcial mantiene estado base y renderiza el resto del panel.
  - Corrección de aislamiento de bitácora por usuario autenticado:
    - `frontend/src/servicios/auth.ts`: al guardar sesión, `usuarioId` ahora se persiste como UUID determinístico derivado de `auth.user.id` (evita colisión con UUID de desarrollo compartido).
    - `frontend/src/servicios/api.ts`: si `usuarioId` no existe/no es UUID, deriva automáticamente UUID estable desde `auth.user.id` y lo guarda; evita fallback continuo al mismo `USUARIO_DESARROLLO` para múltiples cuentas.
  - `backend/motor/recalibracion.py`: fix SQL para filtros opcionales de `modelo_version_id` (`::int`) evitando error PostgreSQL `could not determine data type of parameter` al recalibrar sin versión explícita.
  - `backend/motor/recalibracion.py`: robustez numérica en Platt scaling (sigmoid estable) para evitar `OverflowError: math range error` durante entrenamiento.
  - `backend/motor/recalibracion.py`: fix de compatibilidad UUID en búsqueda de calibrador existente (evita error `'UUID' object has no attribute 'replace'`).
  - Calibración ejecutada sobre datos reales (`origen=API_USUARIO`) para `Q1`, `Q2`, `Q3`, `Q4` y `COMPLETO`; quedan 5 calibradores activos (`platt`).
  - Verificación CORS endpoint pagos desde frontend local (`localhost:5173` y `127.0.0.1:5173`) con respuesta incluyendo `Access-Control-Allow-Origin`.

- Reestructura completa de la home pública `/` (Doc 06):
  - `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx` se rediseña para enfoque producto/conversión Visitante → Base → Premium.
  - Se elimina el enfoque de dashboard público (KPIs personales, win rate, confianza operativa y madurez por competición) y se reemplaza por narrativa de valor:
    - Hero principal con propuesta de valor + CTA principal/secundaria.
    - Bloque de capacidades reales del sistema (análisis, bitácora, dashboard, configuración y profundidad avanzada).
    - Bloque de progresión por tiers (Visitante/Base/Premium).
    - Bloque de organización de módulos del producto.
    - Bloque Premium alineado a profundidad (comparativas multi-mercado, contexto histórico extendido, priorización operativa).
    - CTA final de cierre de home.
- Alineación de rutas de entrada:
  - `frontend/src/App.tsx`: `/` se mantiene como home pública del producto.
  - `frontend/src/App.tsx`: `/centro-analitico` redirige a `/`.
  - `frontend/src/App.tsx`: rutas de rebote (`/chat` y fallback `*`) vuelven a `/` para consistencia con Doc 06.
- Validación técnica ejecutada en frontend:
  - `npm run lint`
  - `npm run build`

## 2026-03-30
- Cierre de Fase 8 (hardening + QA contractual final):
  - Nuevo test unitario `backend/tests/test_access_policy_tiers.py` para validar reglas de acceso por tier/capability y estado fuera de alcance de `chat.contextual`.
  - Validación backend de consistencia ejecutada con `python3 -m py_compile ...` y assertions runtime de policy con `PYTHONPATH=backend`.
  - Cierre documental de QA contractual final en `docs/reportes/FASE_8_HARDENING_QA_FINAL_2026-03-30.md`.
  - Nota de entorno: `pytest` no disponible en esta VM (`command not found`), por lo que se dejó prueba unitaria agregada y validación runtime equivalente ejecutada.
- Validación técnica de cierre de fase en verde:
  - `python3 -m py_compile backend/servicios/access_policy.py backend/servicios/access_tiers.py backend/api/rutas_access.py backend/api/rutas_premium.py backend/api/rutas_product_analytics.py`
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 7 (embudo y analítica de conversión):
  - `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx` agrega evento normalizado `public_center_viewed` (manteniendo compatibilidad con `public_center_view`).
  - `frontend/src/componentes/paginas/PaginaOnboarding.tsx` integra `onboarding_started` y `onboarding_completed` en product analytics con metadata de destino.
  - `frontend/src/componentes/paginas/PaginaLogin.tsx` registra `base_consumption_started` en login/registro exitoso.
  - `frontend/src/componentes/moleculas/PanelDepthPremium.tsx` registra `premium_layer_interaction` (view/click_cta) por módulo y estado premium.
  - `frontend/src/hooks/useGateNavigation.ts` registra `premium_activation_intent` al interactuar con capability `premium.depth`.
  - Integraciones por módulo en `PaginaPrincipal`, `PaginaFutbol` y `AnalisisPartidoFutbol` para atribución de conversión (`nba|futbol|futbol_partido`).
  - Evidencia de cierre: `docs/reportes/FASE_7_EMBUDO_ANALITICA_CONVERSION_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 6 (subestados Base por onboarding) alineado al contrato funcional del doc 06:
  - `frontend/src/App.tsx`: `RutaConOnboarding` redirige a `/onboarding` preservando `from` para continuidad del flujo.
  - `frontend/src/componentes/paginas/PaginaOnboarding.tsx`: onboarding usa `useLocation/useNavigate`, muestra contexto de retorno y al finalizar vuelve al destino intentado (fallback `/dashboard`).
  - Evidencia de cierre: `docs/reportes/FASE_6_ONBOARDING_SUBESTADOS_BASE_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 5 (depth layers premium dentro de módulos existentes):
  - Nuevo componente reusable `frontend/src/componentes/moleculas/PanelDepthPremium.tsx` (y export en `moleculas/index.ts`) para expresar la capa depth premium con los tres bloques oficiales: comparativas multi-mercado, contexto histórico extendido y priorización operativa avanzada.
  - Integración de depth premium en `frontend/src/componentes/paginas/PaginaPrincipal.tsx` (NBA), `frontend/src/componentes/paginas/PaginaFutbol.tsx` (módulo fútbol) y `frontend/src/componentes/paginas/AnalisisPartidoFutbol.tsx` (análisis de partido).
  - CTA de depth alineado a gate `premium.depth` sin crear rutas premium separadas.
  - Evidencia de cierre: `docs/reportes/FASE_5_DEPTH_LAYERS_PREMIUM_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 4 (implementación por vistas contra matriz funcional del doc 06):
  - Se valida cumplimiento funcional por vista para `/`, `/app`, `/dashboard`, `/bitacora`, `/configuracion`, `/futbol`, `/futbol/partidos/:id`, `/futbol/bitacora`, `/futbol/dashboard`, `/login` y `/onboarding`.
  - `frontend/src/componentes/paginas/PaginaLogin.tsx` alinea link de exploración pública al shell visitante oficial `/`.
  - `frontend/src/componentes/paginas/PaginaDashboardUsuario.tsx` alinea atajo “Centro analítico” a `/`.
  - Evidencia de cierre: `docs/reportes/FASE_4_MATRIZ_VISTAS_TIERS_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 3 (header + navegación global tier-aware) alineado al contrato funcional `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`:
  - `frontend/src/componentes/organismos/Encabezado.tsx` ahora responde al tier real (`INVITADO|BASE|PREMIUM`) con indicador de estado de cuenta visible.
  - Corrección de rutas y estado activo de dashboard por deporte (NBA `/dashboard`, Fútbol `/futbol/dashboard`).
  - Navegación al centro público consolidada en `/`.
  - CTA visitante del header se mantiene por gate contextual de acción protegida, evitando rebote agresivo a login.
  - Evidencia de cierre: `docs/reportes/FASE_3_HEADER_NAVEGACION_TIER_AWARE_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 2 (gates UX y visibilidad progresiva) alineado al contrato funcional `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`:
  - `frontend/src/servicios/accessPolicy.ts` incorpora catálogo de copy permitido Base/Premium y nuevo `obtenerGateConfig(...)` para centralizar tipo de gate, CTA y destinos.
  - `frontend/src/contextos/GatePromptContext.tsx` diferencia visual/semánticamente `BASE_REQUIRED` vs `PREMIUM_REQUIRED` vs `DISABLED`.
  - `frontend/src/hooks/useGateNavigation.ts` elimina decisión manual de CTA/rutas y consume configuración central, enviando además `gateType` en evento `gate_blocked`.
  - Evidencia de cierre: `docs/reportes/FASE_2_GATES_UX_VISIBILIDAD_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Cierre de Fase 1 (policy central de capabilities/tier) alineado al contrato funcional `docs/roadmap_inmediato/06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM.md`:
  - Nuevo módulo backend `backend/servicios/access_policy.py` como fuente única de capabilities, tier mínimo y tipos de gate (`BASE_REQUIRED`, `PREMIUM_REQUIRED`, `DISABLED`).
  - `backend/servicios/access_tiers.py` agrega `exigir_capability(...)` con 403 tipado y `exigir_premium(...)` delega en capability `premium.depth`.
  - `backend/api/rutas_access.py` deja lógica duplicada, usa evaluación central y expone `GET /api/access/policy` + `GET /api/access/capability-check` con `required_tier` y `gate`.
  - `frontend/src/servicios/accessPolicy.ts` migra a catálogo único `CAPABILITY_META` con resolución central de habilitación por tier y tipo de gate.
  - Evidencia de cierre: `docs/reportes/FASE_1_POLICY_CAPABILITIES_TIERS_2026-03-30.md`.
- Validación técnica de cierre de fase en verde:
  - `python3 -m py_compile backend/servicios/access_policy.py backend/servicios/access_tiers.py backend/api/rutas_access.py backend/api/rutas_premium.py`
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run build`
- Ajuste de consistencia con el plan de tiers visitante/premium en runtime:
  - `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx` cambia CTAs de visitante para usar gates por acción (`useGateNavigation`) en vez de navegar directo a `/login`.
  - `frontend/src/componentes/organismos/Encabezado.tsx` reemplaza CTA de invitado por acción protegida con gate (`analisis.nba.base` / `futbol.base`) en lugar de envío directo a login.
  - `frontend/src/App.tsx` consolida chat fuera de alcance redirigiendo `/chat` a `/` (sin ruta operativa de chat).
  - `frontend/src/componentes/paginas/index.ts` elimina export de `PaginaChat` para evitar exposición accidental en navegación de páginas.
- Estado documental actualizado en `docs/arquitectura/ESTADO_PROYECTO.md` con la corrección de enforcement visitante/gates.
- Validación técnica ejecutada: `npm --prefix frontend run lint` y `npm --prefix frontend run build` en verde.

## 2026-03-27
- Decisión de producto: chat queda fuera de alcance en la fase actual y debe permanecer oculto en UI hasta nueva instrucción.
- Frontend ajustado para retirar chat de navegación:
  - `frontend/src/componentes/organismos/Encabezado.tsx` elimina botón/entrada de Chat.
  - `frontend/src/App.tsx` elimina carga de `PaginaChat` y redirige `/chat` hacia `/dashboard`.
- Documento de tiers actualizado para reflejar chat como **fase futura** y no disponible hoy:
  - `docs/roadmap_inmediato/inputs_producto/ACCESO_POR_TIER_MODO_VISITANTE_Y_CAPA_PREMIUM.md`.
- Estado de proyecto actualizado en B5 para dejar explícito: backend preservado, UI oculta y reactivación sujeta a instrucción explícita.
- Backend endurecido para evitar uso manual de chat:
  - `backend/app.py` introduce flag `CHAT_ENABLED` (default `false`) y no registra router `/api/chat/*` cuando está deshabilitado.
  - `GET /salud` expone `configuracion.chat_enabled` para trazabilidad operativa.
  - Variables de entorno actualizadas: `backend/.env.example` y `deploy/staging/staging.env.example` con `CHAT_ENABLED=false`.
- Nuevo plan de ejecución del rediseño por tiers:
  - `docs/roadmap_inmediato/05_PLAN_EJECUCION_TIERS_VISITANTE_PREMIUM.md`.
- Inicio de Fase A (policy central de acceso) en frontend:
  - Nuevo servicio `frontend/src/servicios/accessPolicy.ts` con catálogo de capacidades por tier (`INVITADO|BASE|PREMIUM`) y control explícito de `chat.contextual` deshabilitado.
  - Nuevo contexto `frontend/src/contextos/AccessPolicyContext.tsx` para resolver tier desde sesión + estado de plan.
  - `frontend/src/main.tsx` integra `ProveedorAccessPolicy`.
  - `frontend/src/App.tsx` migra rutas principales a validación por capacidad (`RutaConCapacidad`) además de auth/onboarding.
- Extensión de Fase A hacia acciones UI (gates por acción):
  - `frontend/src/componentes/organismos/Encabezado.tsx` aplica `navegarConGate(...)` para análisis/bitácora/dashboard/configuración con redirección por capacidad (login para invitado, dashboard para base sin capacidad).
  - `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx` aplica gates por capacidad en CTAs de análisis/bitácora/capa premium.
- Inicio de Fase B (entrada principal como shell visitante):
  - `frontend/src/App.tsx`: `/` ahora carga directamente `PaginaCentroAnalitico` como entrada pública real del sistema.
  - `frontend/src/App.tsx`: `/centro-analitico` redirige a `/` para evitar doble entrypoint.
  - `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx`: se absorbe bloque de introducción tipo landing dentro del shell visitante (mensaje de valor + resumen visitante/base/premium + CTAs de cuenta).
  - `frontend/src/componentes/organismos/Encabezado.tsx`: ajuste de estado activo para que `/` se trate como centro analítico (no análisis profundo).
- Inicio de Fase C (gating reutilizable por acción):
  - Nuevo hook `frontend/src/hooks/useGateNavigation.ts` centraliza navegación con gate + redirección + toast de contexto.
  - `frontend/src/servicios/accessPolicy.ts` agrega `obtenerGateCopy(...)` con mensajes funcionales por capacidad y estado (visitante/base).
  - `Encabezado` y `PaginaCentroAnalitico` migran a gate reutilizable para eliminar lógica duplicada y estandarizar copy de bloqueo.
- Extensión de Fase C a dashboard:
  - `frontend/src/componentes/paginas/PaginaDashboardUsuario.tsx` integra `useGateNavigation` para atajos de análisis/bitácora y CTA principal "Ir al análisis".
  - Se consolida experiencia de gating consistente (mismo flujo de mensaje + redirección) en superficies clave.
- Extensión adicional de Fase C en superficies operativas:
  - `frontend/src/componentes/paginas/BitacoraFutbol.tsx` aplica gate reutilizable en navegación de retorno a módulo fútbol.
  - `frontend/src/componentes/paginas/DashboardFutbol.tsx` aplica gate reutilizable en navegación de retorno a módulo fútbol.
  - `frontend/src/componentes/paginas/PaginaPrincipal.tsx` aplica gate reutilizable en CTA de configuración de bankroll (`configuracion.base`).
  - `frontend/src/componentes/paginas/PaginaDashboardUsuario.tsx` unifica CTA de suscripción/gestión de plan hacia configuración mediante gate.
- Cierre funcional de Fase C con componente visual único de gate:
  - Nuevo `frontend/src/contextos/GatePromptContext.tsx` renderiza modal/panel global para bloqueos por tier con CTA contextual.
  - `frontend/src/hooks/useGateNavigation.ts` migra de toast a gate modal reutilizable con acciones diferenciadas visitante/base/premium.
  - `frontend/src/main.tsx` integra `ProveedorGatePrompt` para disponibilidad global del gate visual.
- Ejecución de Fase D (separación Base vs Premium por profundidad):
  - `frontend/src/componentes/paginas/PaginaDashboardUsuario.tsx` agrega bloque condicional de "Capas premium activas" para PREMIUM y teaser claro para BASE.
  - CTA de upgrade ahora usa gate `premium.depth` (flujo explícito de frontera base → premium).
  - `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx` refuerza copy diferencial BASE vs PREMIUM sin bloquear flujo esencial.
- Cierre de Fase E (hardening de acceso):
  - Backend incorpora política central de tiers en `backend/servicios/access_tiers.py`.
  - Nuevo router premium `backend/api/rutas_premium.py` con enforcement server-side:
    - `GET /api/premium/capas-depth` (requiere premium activo, 403 para base)
    - `GET /api/premium/estado-tier`.
  - `backend/app.py` integra `router_premium`.
  - Frontend consume señal premium real con `frontend/src/servicios/premium.ts` y `PaginaDashboardUsuario`.
  - Reporte de auditoría de bypass: `docs/reportes/FASE_E_HARDENING_ACCESO_2026-03-28.md`.
- Cierre de Fase F (aceptación final):
  - Instrumentación de eventos de producto en frontend con `frontend/src/servicios/productAnalytics.ts`.
  - `useGateNavigation` registra eventos `gate_allowed` y `gate_blocked`.
  - `PaginaCentroAnalitico` registra `public_center_view` con contexto de tier/deporte.
  - Checklist de aceptación final en `docs/reportes/FASE_F_ACEPTACION_FINAL_TIERS_2026-03-28.md`.
- Hardening adicional post-auditoría (cobertura de pendientes detectados):
  - Backend agrega `backend/api/rutas_access.py` con `GET /api/access/capability-check` para verificación server-side de capability↔tier.
  - Backend agrega `backend/api/rutas_product_analytics.py` para ingesta de eventos (`POST /api/product-analytics/events`) y se integra en `app.py`.
  - Frontend `productAnalytics.ts` ahora hace envío best-effort a backend (además de buffer local) para evitar telemetría solo local.
  - Corrección de coherencia funcional: `App.tsx` enruta `/futbol/bitacora` a `BitacoraFutbol` (antes apuntaba a bitácora general).
- Validación técnica: `python3 -m py_compile` (backend), `npm run lint` y `npm run build` (frontend) OK tras cierre y hardening adicional.

## 2026-03-26
- C1/B1 pagos endurecido para evento real de Mercado Pago:
  - `POST /api/pagos/webhook/mercadopago` ahora valida firma real de MP (`X-Signature` con `ts/v1` + `X-Request-Id` + `data.id`) en lugar de HMAC del payload interno.
  - Webhook ahora consulta `GET https://api.mercadopago.com/v1/payments/{id}` para obtener estado efectivo y `external_reference` antes de persistir/activar.
  - Idempotencia mantenida por `(external_reference, payment_id, status)`.
- Persistencia de pagos preparada para producción en PostgreSQL/Neon:
  - `backend/servicios/pagos_store.py` agrega driver `postgres` (`PAGOS_STORE_DRIVER=postgres`) con tablas `payment_intents`, `subscriptions`, `payment_events` en Postgres.
  - Se conserva driver `sqlite` para desarrollo local.
- Mapeo operativo de estados MP reforzado para gate de suscripción:
  - `approved/authorized -> active`,
  - `pending/in_process -> past_due`,
  - `rejected/cancelled/refunded/charged_back -> inactive`.
- Cierre formal de A1 (staging + smoke real): despliegue ejecutado en host con Docker y evidencia en `docs/reportes/A1_SMOKE_STAGING_2026-03-26T14-12-43Z.md`.
- Corrección del script de smoke A1: se reemplaza verificación de `GET /api/pagos/feature-gate` (ahora requiere query+auth) por `GET /api/pagos/matriz-estados` para mantener smoke reproducible sin sesión.
- Endurecimiento de scripts operativos B3/B4 para ejecución real:
  - `scripts/b3_ciclo_semanal.sh` ahora soporta `X-Usuario-Id`, usa `python3` portable y marca explícitamente ciclos sin muestra como no computables para cierre formal.
  - `scripts/b4_ciclo_24h_reporte.sh` ahora soporta `X-Usuario-Id` y usa `limit=100` (tope válido del endpoint historial).
- Evidencia operativa nueva generada:
  - `docs/reportes/B3_CICLO_SEMANAL_2026-03-26T14-16-17Z.md`
  - `docs/reportes/B4_CICLO_24H_2026-03-26T14-16-17Z.md`
  - `docs/reportes/B6_PREFLIGHT_2026-03-26T14-14-04Z.md` (hallazgos: faltan `MP_ACCESS_TOKEN` y `MP_WEBHOOK_SECRET` en staging.env).
- Cierre operativo de Ola 1 (P1/P2/P3) y arranque de Ola 2 (P4/P6/P8) en superficies públicas principales.
- `PaginaPublicaProducto` reforzada con tabla comparativa visitante/registrado/premium para definir mejor el valor por nivel de acceso.
- `PaginaCentroAnalitico` enriquecida con:
  - madurez de fútbol por competición (estable / en validación / lab),
  - mayor visibilidad de inteligencia operativa,
  - definición funcional inicial de premium como capa de profundidad (no solo desbloqueo).
- `PaginaDashboardUsuario` reforzada para Ola 2:
  - bloque explícito de ruta fútbol sin maquillaje,
  - bloque de evolución premium con CTA de suscripción/gestión de plan,
  - continuidad entre valor público y valor para usuario registrado.
- `PaginaConfiguracion` reforzada para Ola 2:
  - bloque de gobernanza de madurez fútbol por estados,
  - bloque de estado de plan con narrativa premium orientada a profundidad de producto.
- `PaginaLogin` reforzada con señal comercial/operativa de Ola 2:
  - credibilidad anti-humo,
  - fútbol sin maquillaje por madurez,
  - premium como profundidad funcional.
- `PaginaDashboardUsuario` reforzada para inicio de P7:
  - baseline técnico 1X2 visible (`hitRateSinPush`, finalizadas) como referencia para futuras mejoras de modelo/motor.
  - recarga forzada disponible para evitar lecturas obsoletas durante revisión técnica.
- `frontend/src/servicios/futbol/metricas.ts` incorpora caché de 5 min (sessionStorage) para `obtenerResumenCalidad1x2`, reduciendo costo/latencia en navegación repetida (Ola 3 rendimiento).
- `frontend/src/servicios/observabilidad.ts` incorpora caché corta (60s) para salud backend y observabilidad HTTP, con bypass por refresh forzado en dashboard fútbol.
- `PaginaCentroAnalitico` añade bloque de "confianza operativa" con nivel interpretativo basado en muestra resuelta y win rate (mejora de visibilidad de inteligencia, P6).
- `PaginaDashboardUsuario` añade:
  - alerta accionable de onboarding pendiente,
  - atajos operativos (análisis, bitácora, centro analítico) para reducir fricción y TTV (Ola 3 UX).
  - guía operativa sugerida basada en baseline 1X2 (traducción práctica de señal técnica para control de exposición).
  - KPIs de rendimiento cliente (DOM Ready / Load Event / Transferencia) para seguimiento técnico visible en producto.
- Cierre formal de Ola 2:
  - umbrales de promoción fútbol por competición documentados en P4,
  - matriz funcional consolidada visitante/registrado/premium en P8,
  - estado de proyecto actualizado a Ola 2 cerrada.
- Cierre formal de Ola 3 (alcance frontend/producto):
  - reporte final actualizado en `docs/auditoria/REPORTE_CIERRE_OLA3_P7_P9.md`,
  - benchmark documentado en `docs/auditoria/BENCHMARK_OLA3_FRONTEND.md`,
  - estado de proyecto actualizado a Ola 3 `CERRADA`.
- Se crea panel operativo permanente de ejecución inmediata en `docs/roadmap_inmediato/` con índice y 8 bloques priorizados (A1/B3/B4/B6/P7/P9/A3/B5).
- Inicio de ejecución de A1 real:
  - runbook operativo detallado en `docs/roadmap_inmediato/01_A1_STAGING_SMOKE_REAL.md`,
  - script reproducible `scripts/a1_smoke_staging.sh` que genera reporte automático en `docs/reportes/`.
- Inicio operativo de B3 y B4:
  - `scripts/b3_ciclo_semanal.sh` para evidencia semanal de estabilidad por liga,
  - `scripts/b4_ciclo_24h_reporte.sh` para reporte de ciclo 24h de notificaciones,
  - runbooks actualizados en `docs/roadmap_inmediato/02_B3_CIERRE_FORMAL.md` y `03_B4_CIERRE_24H_SLO.md`.
- Inicio operativo de B6 hardening:
  - `scripts/b6_preflight_hardening.sh` con verificación de secretos/artefactos,
  - runbook y checklist en `docs/operacion/B6_*`,
  - primer reporte generado: `docs/reportes/B6_PREFLIGHT_2026-03-26T02-51-48Z.md`.
- Optimización adicional de frontend (Ola 3):
  - extracción lazy del gráfico ROI de `DashboardFutbol` a `GraficoRoiTemporalFutbol` para reducir costo inicial del dashboard.
  - impacto medido: `DashboardFutbol` de ~412.41 kB a ~28.51 kB (el costo pesado queda en chunk lazy separado).
- Inicio operativo de sunset legacy (A3 post-cierre):
  - script `scripts/a3_monitoreo_legacy.sh` para seguimiento diario de tasa legacy,
  - runbook actualizado en `docs/roadmap_inmediato/07_A3_SUNSET_LEGACY_REAL.md`.
- Inicio de Ola 3 (P7/P9):
  - `frontend/src/App.tsx` migrado a carga diferida de módulos pesados (`React.lazy` + `Suspense`) para mejorar rendimiento percibido y preparar optimización de bundle.
  - `PaginaPrincipal` optimizada con carga diferida de componentes pesados de estadísticas (`TablaEstadisticasEquipos`, `HistorialEquipo`) para reducir costo inicial cuando el usuario entra por la pestaña de análisis.
  - ajuste de imports directos en `App.tsx` (evitando barrel import estático) para no romper el code-splitting de rutas.
  - impacto observado en build: chunk de `PaginaPrincipal` baja de ~179.8 kB a ~159.6 kB.
  - actualización de estado y avances en documentos `P7_MEJORA_MODELO_Y_MOTOR.md` y `P9_UX_Y_RENDIMIENTO.md`.
- Documentación comercial pública actualizada con avance de ejecución en P1/P2/P3/P4/P6/P8.
- `ESTADO_PROYECTO.md` actualizado para reflejar Ola 1 cerrada y Ola 2 en ejecución.

## 2026-03-25
- Se crea el plan público de negocio por prioridades P1–P9 en `docs/comercial/publico/` con índice y criterios por ola (P1/P2/P3 → P4/P6/P8 → P7/P9).
- Se alinea la fuente de verdad para incluir el plan público como referencia activa:
  - `docs/FUENTE_DE_VERDAD_ACTUAL.md`
  - `docs/arquitectura/ESTADO_PROYECTO.md`
  - `docs/auditoria/RUTA_AUDITORIA_C0_C7.md`
- Ejecución funcional de Ola 1 en superficies principales de producto (sin tocar IA):
  - flujo público habilitado: `/` como landing de valor y `/centro-analitico` en modo visitante controlado,
  - nueva capa de identidad visitante trazable local (`frontend/src/servicios/visitante.ts`) con métricas de entrada (landing/centro),
  - punto de bloqueo explícito: visitante no accede a análisis operativo (`/app`), bitácora ni funciones personales sin login,
  - `PaginaLogin` refuerza propuesta de valor y ruta de exploración visitante limitada,
  - `PaginaPrincipal` incorpora banner de credibilidad (sin promesas de ganancias fáciles, NBA maduro / fútbol beta-lab).
- Nota: el ajuste previo de límites en Chat queda como hardening secundario; el eje freemium de Ola 1 se mueve al frente principal público.

## 2026-03-24
- C0 ejecutado: realineación formal de go-live comercial.
- Nueva ADR `docs/arquitectura/ADR-005-alcance-comercial-minimo-c0.md` con decisión explícita de alcance mínimo:
  - bloqueantes de caja: C1, C2, C3, C4, C7
  - paralelo no bloqueante: C5, C6
- Contradicción formal resuelta entre dependencia histórica de B7 y estrategia actual (B3/B4/B5 no bloquean primer peso).
- Riesgo de persistencias temporales formalizado para inventario/decisión en C2.
- Fuente de verdad y estado del proyecto actualizados para reflejar secuencia C0–C7.
- `PLAN_EJECUCION_BLOQUES_V3.md` marcado como histórico/superado para decisiones de go-live.
- C1 ejecutado en capa técnica (pagos productivos equivalentes trazables), pendiente validación manual real para cierre total:
  - idempotencia de webhook por evento (`payment_events`),
  - matriz formal de estados de pago/suscripción/gate,
  - feature-gating consistente por suscripción,
  - evidencia E2E reproducible del primer pago equivalente (`docs/reportes/C1_E2E_PRIMER_PAGO_VALIDACION_EQUIVALENTE_2026-03-24.md`, 6/6 tests),
  - template oficial de cierre manual (`docs/reportes/C1_CIERRE_MANUAL_MERCADOPAGO_TEMPLATE.md`).
- Documentación operativa C1 agregada:
  - `docs/operacion/FLUJO_REAL_PAGOS_C1.md`
  - `docs/operacion/C1_MATRIZ_ESTADOS_Y_FALLOS.md`
- C2 ejecutado (hardening y persistencia):
  - matriz formal de persistencias launch-critical y decisiones por componente,
  - estrategia de persistencia productiva con aceptación temporal mitigada de SQLite,
  - scripts operativos de backup/restore + test real de restore,
  - runbook operativo con rollback y política mínima de secretos,
  - observabilidad mínima de componentes críticos (`GET /api/operacion/c2/health-critical`),
  - evidencia de restore test en `docs/reportes/C2_BACKUP_RESTORE_TEST_2026-03-24.md`.
- C3 ejecutado (cumplimiento comercial mínimo):
  - documento rector comercial mínimo por flujos premium,
  - matriz de cobertura legal/comercial por flujo premium,
  - checklist de validación legal-operativa previo a go-live,
  - revisión de consistencia entre UI, backend y documentación legal/comercial.
- C4 ejecutado (activación y entrada de valor):
  - inventario formal del flujo actual visitante -> registro -> onboarding -> dashboard/premium,
  - matriz de capacidades por tipo de usuario (visitante/registrado/suscrito),
  - definición de puntos de valor inicial antes del muro total,
  - KPIs de activación orientados a valor real (TTV, activación útil, valor entendido),
  - revisión de copy alineada a narrativa profesional (sin hype de rentabilidad),
  - comunicación explícita de NBA frente principal y fútbol en laboratorio controlado.
- C5 ejecutado (paridad operativa de fútbol):
  - endpoint canónico `GET /api/futbol/metricas/roi-temporal` para serie real de ROI acumulado,
  - `DashboardFutbol` migrado de serie simulada a consumo backend real,
  - contrato canónico de fútbol documentado,
  - checklist de madurez y criterios de promoción comercial de fútbol agregados.
- C6 ejecutado (centro analítico multideporte v1):
  - nueva vista unificada `/centro-analitico` con shell común, selector de deporte y KPIs base compartidos,
  - navegación común reforzada en encabezado (acceso directo a Centro),
  - madurez visible por deporte (NBA maduro, fútbol beta/lab) sin falsa equivalencia comercial,
  - contrato base de métricas comunes y documentación de inventario/madurez/reportes de C6.
- Preflight de C7 formalizado sin ejecutar C7:
  - C1 se mantiene EN_CURSO y bloqueado por dependencia de dominio/URL pública para validación manual real de MP,
  - C7 permanece bloqueado hasta cierre manual evidenciado de C1,
  - nueva ruta de auditoría C0–C7 en `docs/auditoria/RUTA_AUDITORIA_C0_C7.md`.
- Clarificación documental C1/C7 para eliminar ambigüedad:
  - diferencia explícita entre validación equivalente reproducible, validación manual homologada y validación manual real,
  - regla formal: solo validación manual real habilita C1=CERRADO y apertura de C7,
  - normalización de nomenclatura C0–C7 (comercial) vs B1–B7 (histórico técnico) en `ESTADO_PROYECTO.md`.

## 2026-03-18
- Inicio de B5 (chat contextual):
  - Nuevo módulo `backend/servicios/chat_contexto.py` con persistencia de mensajes (SQLite), ventana deslizante y motor local/mock inteligente.
  - Guardrails activos en B5: disclaimer fijo y bloqueo de prompts de advice sensible/riesgo extremo.
  - Nuevas rutas backend:
    - `POST /api/chat/mensaje`
    - `GET /api/chat/historial`
    - `POST /api/chat/reset`
  - Router integrado en `backend/app.py`.
  - Nuevo esquema `backend/esquemas/chat.py`.
  - Tests API nuevos: `backend/tests/api/test_chat_endpoints.py`.
- Continuación B5 (frontend):
  - Nueva página `frontend/src/componentes/paginas/PaginaChat.tsx` con UI de chat, historial, reset de contexto y disclaimer visible.
  - Nuevo servicio `frontend/src/servicios/chat.ts` para integrar envío/historial/reset.
  - Ruta protegida `/chat` agregada en `App.tsx` y acceso desde `Encabezado`.
  - Validación frontend ejecutada: `npm run lint` + `npm run build` OK.
- Continuación B5 (contexto de negocio real en motor local):
  - `rutas_chat.py` ahora inyecta señales de negocio en tiempo de respuesta (métricas de entrega B4 + KPIs onboarding B2).
  - `chat_contexto.py` ajusta respuestas de tipo KPI/métricas para incluir contexto operativo real cuando está disponible.
  - Tests de chat ampliados para validar presencia de contexto de negocio en respuesta de KPI.
  - Validación backend ejecutada: suite auth+chat+notificaciones+smoke en verde.
- Continuación B5 (resumen automático de contexto largo):
  - Nuevo compactador de ventana en `chat_contexto.py` (`compactar_ventana_con_resumen`) para comprimir historial cuando supera el límite configurado.
  - `POST /api/chat/mensaje` ahora responde `summary_applied` y utiliza resumen contextual al generar respuesta.
  - Tests ampliados para validar aplicación de resumen en conversaciones largas.
- Fase 2 B5 (interfaz desacoplada de proveedor):
  - Nuevo módulo `backend/servicios/chat_provider.py` con contrato `ChatProvider`.
  - Modos soportados por env `CHAT_PROVIDER_MODE`:
    - `local` → motor actual (`local-mock`)
    - `external` → placeholder explícito (`external-placeholder`) para futuro adaptador LLM real.
  - `POST /api/chat/mensaje` ahora reporta `provider` en respuesta para trazabilidad operativa.
  - Tests ampliados para validar modo local y modo external-placeholder.
- Mejora profesional B5 (calidad de respuesta por objetivo):
  - `chat_contexto.py` ahora genera planes accionables de 48h por objetivo explícito:
    - rentabilidad
    - disciplina
    - aprendizaje
  - Respuesta de recomendaciones genéricas ahora pide objetivo para convertirse en plan concreto.
  - Tests de chat ampliados para validar plan de rentabilidad en formato estructurado.

- Inicio de B4 (notificaciones MVP):
  - Nuevas rutas backend en `api/rutas_notificaciones.py`:
    - `GET /api/notificaciones/preferencias`
    - `PUT /api/notificaciones/preferencias`
    - `POST /api/notificaciones/enviar-prueba`
    - `GET /api/notificaciones/historial`
  - Nuevo store `backend/servicios/notificaciones_store.py` para preferencias e historial de envíos.
  - Integración de router en `backend/app.py`.
  - Nuevo esquema `backend/esquemas/notificaciones.py`.
  - Tests nuevos: `backend/tests/api/test_notificaciones_endpoints.py`.
- Continuación B4: jobs y reintentos básicos para notificaciones email:
  - Cola persistente `notificaciones_cola` con `intentos`, `max_intentos`, `proximo_intento_at` y `last_error`.
  - Nuevos endpoints:
    - `POST /api/notificaciones/encolar-prueba`
    - `POST /api/notificaciones/procesar-cola`
    - `POST /api/notificaciones/scheduler/encolar`
  - Scheduler por tipo de alerta (`alertas_partidos`, `alertas_suscripcion`, `resumen_semanal`) respetando preferencias por usuario.
  - Procesamiento con backoff básico y trazabilidad en historial (`enviado`, `pendiente`, `fallido`, `omitido`).
- Automatización operativa B4 (sin disparo manual):
  - Nuevo script `scripts/notificaciones_scheduler_tick.sh` para ejecutar `scheduler/encolar` + `procesar-cola` en un solo paso.
  - Nuevo target `make notificaciones-scheduler-tick`.
  - Plantilla de cron en `deploy/staging/cron-notificaciones.example` para ejecución periódica por tipo de alerta.
- B4 frontend conectado en Configuración:
  - Nueva integración `frontend/src/servicios/notificaciones.ts`.
  - `PaginaConfiguracion` ahora permite cargar/editar preferencias de notificaciones (toggles), guardar cambios y disparar prueba de envío.
  - Validación frontend ejecutada: `npm run lint` + `npm run build` OK.
- Endurecimiento operativo B4:
  - Nuevo endpoint `GET /api/notificaciones/metricas-entrega` (totales por estado, tasa de entrega y desglose por tipo).
  - Límites de reintentos por tipo configurables vía env:
    - `NOTIF_MAX_INTENTOS_ALERTAS_PARTIDOS`
    - `NOTIF_MAX_INTENTOS_ALERTAS_SUSCRIPCION`
    - `NOTIF_MAX_INTENTOS_RESUMEN_SEMANAL`
  - Tests de notificaciones ampliados para validar métricas y límites por tipo.
- UX B4 en frontend refinada:
  - `PaginaConfiguracion` muestra métricas de entrega (24h) con semáforo de salud (verde/amarillo/rojo), tasa de entrega y totales por estado.
  - La UI recarga métricas al guardar preferencias y al enviar notificación de prueba.
  - Servicio frontend extendido con `obtenerMetricasEntrega()` en `frontend/src/servicios/notificaciones.ts`.
- Criterio formal de cierre B4 definido y evidenciado:
  - Reporte creado: `docs/reportes/B4_SLO_CICLO_2026-03-18T13-30-08Z.md`.
  - SLO de cierre establecido (tasa de entrega, ratio fallidos, reprogramados y contrato API).
  - Estado B4 actualizado para pasar a cierre tras 1 ciclo operativo real que cumpla SLO.
- Inicio de B3 (estabilización fútbol + cross-liga v1):
  - Nuevo módulo `backend/servicios/b3_estabilizacion_futbol.py` con:
    - combinación de valor cross-liga ponderada por competición,
    - ajuste de probabilidad por tamaño de muestra total/relevante,
    - nivel de confianza B3 por cobertura de datos.
  - Integración en `backend/api/rutas_analisis_futbol.py` para usar combinación cross-liga y confianza/recomendación ajustada por muestra relevante.
  - Test unitario nuevo: `backend/tests/test_b3_estabilizacion_futbol.py`.
- Continuación B3: policy gate semanal por drift/calidad de fútbol por liga:
  - Nuevo endpoint `GET /api/futbol/metricas/b3-estabilidad` con clasificación `estable|warning|critico|insuficiente` por liga.
  - Regla de criticidad: degradación semanal de Brier (abs >= 0.03 y rel >= 15%) con muestra mínima por ventana.
  - Salida incluye `gate_aprobado` para decisión operativa del ciclo.
  - Test unitario nuevo: `backend/tests/test_b3_estabilidad_metricas.py`.
- Automatización de evidencia B3 por ciclo semanal:
  - Nuevo script `scripts/reporte_b3_estabilidad.sh` que genera reporte en `docs/reportes/B3_ESTABILIDAD_<timestamp>.md`.
  - Nuevo target de Makefile: `make reporte-b3-estabilidad`.
  - Primer reporte generado: `docs/reportes/B3_ESTABILIDAD_2026-03-18T12-37-09Z.md`. 
- Cierre formal de B2 (onboarding + dashboard usuario):
  - Estado de bloque actualizado a `CERRADO` en `docs/arquitectura/ESTADO_PROYECTO.md`.
  - Criterio de cierre: onboarding obligatorio + persistencia backend + telemetría de conversión + KPI real de `completion_rate` y `time_to_value` disponible en API/UI.
  - Seguimiento posterior definido como operativo (no bloqueante) para ajuste fino de UX/copy.
- Inicio de B2 (onboarding + dashboard usuario) en frontend:
  - Nueva ruta `/onboarding` con wizard de 3 pasos (perfil base, objetivo principal y control de riesgo inicial).
  - Nueva ruta `/dashboard` con KPIs de rendimiento (totales, resueltas, ganadas, perdidas, push, win-rate) obtenidos desde `GET /api/bitacora/apuestas-analizadas`.
  - Integración de estado de plan en dashboard usando `GET /api/pagos/suscripcion/mia`.
  - Guard de navegación: rutas principales ahora requieren onboarding completado.
- Servicios agregados para B2:
  - `frontend/src/servicios/onboarding.ts`
  - `frontend/src/servicios/pagos.ts`
- Continuación B2: persistencia backend real de onboarding y telemetría de conversión:
  - Nuevas rutas backend `api/rutas_onboarding.py`:
    - `GET /api/onboarding/estado`
    - `POST /api/onboarding/perfil`
    - `POST /api/onboarding/evento`
  - Nuevo store `backend/servicios/onboarding_store.py` con soporte `sqlite|postgres` (drivers por env: `ONBOARDING_STORE_DRIVER`, `ONBOARDING_DB_PATH`).
  - Nuevo esquema `backend/esquemas/onboarding.py` para perfil y eventos de embudo.
  - Integración en `backend/app.py` y nuevo test `backend/tests/api/test_onboarding_endpoints.py`.
  - Frontend ahora sincroniza estado onboarding contra backend (hidratación en auth) y registra eventos `onboarding_started`, `onboarding_completed`, `dashboard_viewed`.
- Limpieza frontend (hooks/deps): se corrigieron warnings `react-hooks/exhaustive-deps` en `SelectorPartido`, `FormularioAnalisis`, `GraficoDistribucion` y `TablaEstadisticasEquipos`.
- KPI real de activación incorporado:
  - Backend: nuevo `GET /api/onboarding/kpis` (usuarios iniciados/completados, `completion_rate_pct`, `time_to_value_minutes_avg`, tamaño de muestra).
  - Frontend dashboard: tarjetas con Completion Rate y Time-to-Value promedio basados en datos reales de eventos.
- Validaciones B2 (persistencia+conversión+KPIs):
  - `backend/.venv/bin/pytest -q backend/tests/api/test_onboarding_endpoints.py backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (18 passed)
  - `npm run lint` ✅ (sin errores)
  - `npm run build` ✅
- Métricas profesionales: `GET /api/metricas/recomendaciones-accion` ahora acepta `max_acciones` (1-50) y normaliza la salida (deduplicación por acción/prioridad/semaforo + orden estable por impacto), evitando planes redundantes en runtime.
- Validación ejecutada del bloque métricas: `backend/.venv/bin/pytest -q backend/tests/test_rutas_metricas.py backend/tests/api/test_metricas_profesionales_endpoints.py` ✅ (12 passed).
- Estado documental actualizado: `docs/PENDIENTES_OPERATIVOS.md` marca como validado el runtime de recomendaciones de acción.
- Inicio de B1 (pagos/suscripción): se implementó backend base con `POST /api/pagos/checkout-session`, `POST /api/pagos/webhook/mercadopago` (validación `X-Signature` HMAC-SHA256), `GET /api/pagos/suscripcion/mia` y `GET /api/pagos/feature-gate`.
- Se añadió persistencia mínima de intents y suscripciones en `backend/servicios/pagos_store.py` (SQLite con `PAGOS_DB_PATH`).
- Validación ejecutada B1 base: `backend/.venv/bin/pytest -q tests/api/test_pagos_endpoints.py tests/api/test_auth_endpoints.py` ✅ (14 passed).
- Cierre A6 (Gate Fase A): se creó `scripts/validar_a6_rca.sh` para ejecutar validación integral automatizada de A2/A3/A4/A5 + frontend (lint/build), generando evidencia en `docs/reportes/A6_RC-A_2026-03-18T07-28-30Z.md` con resultado RC-A APROBADO y 0 bloqueantes P0/P1.
- Cierre A5 (observabilidad operativa): dashboard de fútbol integra scraping de salud/observabilidad (`/salud` + `/api/interno/observabilidad-http`) con tarjetas de estado backend, p95, error rate y alertas activas.
- Se añadió servicio frontend `frontend/src/servicios/observabilidad.ts` para centralizar lecturas operativas de salud y observabilidad HTTP.
- Validación controlada de alertas A5 incorporada con test endpoint `backend/tests/test_observabilidad_http_endpoint.py` (incluye escenario de error-rate > umbral).
- A5 (observabilidad operativa) en progreso: se añadió instrumentación HTTP mínima en `backend/app.py` con captura de latencia por request + status code, y nuevo endpoint `GET /api/interno/observabilidad-http` para exponer p95, error rate (5xx), uptime y alertas por umbral.
- Se creó `backend/observabilidad_http.py` como módulo reusable en memoria para métricas HTTP operativas.
- Se añadieron pruebas `backend/tests/test_observabilidad_http.py` para validar cálculo de p95, error_rate y disparo de alertas.
- Se incorporó al repositorio el plan de ejecución por bloques v3 en `docs/arquitectura/PLAN_EJECUCION_BLOQUES_V3.md`.
- Se creó `docs/arquitectura/ESTADO_PROYECTO.md` como fuente única de estado operativo por bloque.
- Se agregaron ADRs iniciales:
  - `ADR-001-auth.md` (JWT + refresh + reset)
  - `ADR-002-pagos.md` (MercadoPago por foco LATAM + nota Stripe para Europa)
  - `ADR-003-chat-contexto.md` (ventana deslizante N para controlar costo LLM)
- Se inició limpieza de documentación obsoleta para evitar uso de contexto duplicado.
- Se agregó CI básico en GitHub Actions (`.github/workflows/ci.yml`) con:
  - backend smoke tests (`pytest -q tests/test_smoke_api.py`)
  - frontend lint + build (`npm run lint`, `npm run build`)
- Se creó base de staging en Docker:
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `deploy/staging/docker-compose.yml`
  - `deploy/staging/staging.env.example`
- Ajuste de calidad para CI frontend: se eliminó `any` explícito en `PaginaFutbol.tsx` (`ApuestaAnalizada` tipado).
- Validaciones locales ejecutadas:
  - `backend/.venv/bin/python -m pytest -q backend/tests/test_smoke_api.py` ✅ (3 passed)
  - `npm run lint` ✅ (solo warnings de hooks)
  - `npm run build` ✅
- Nota: verificación de `docker compose` pendiente por falta de Docker en este host.
- Se inició bloque A2 con autenticación real base en backend:
  - Nuevas rutas `backend/api/rutas_auth.py`: `register`, `login`, `refresh`, `logout`, `forgot-password`, `reset-password`, `me`.
  - Seguridad añadida en `backend/servicios/auth_seguridad.py` (hash PBKDF2-SHA256 y tokens firmados con expiración).
  - Persistencia inicial de auth en `backend/servicios/auth_store.py` (SQLite staging/dev con revocación de tokens y reset tokens).
  - Router de auth integrado en `backend/app.py`.
  - Esquemas Pydantic en `backend/esquemas/auth.py`.
  - Pruebas API añadidas: `backend/tests/api/test_auth_endpoints.py` ✅ (3 passed).
- Ajuste en staging Docker: soporte de puertos de frontend/backend parametrizados vía `STAGING_FRONTEND_PORT` y `STAGING_BACKEND_PORT`.
- Continuación de A2 en frontend:
  - Contexto de autenticación en `frontend/src/contextos/AuthContext.tsx`.
  - Página de login en `frontend/src/componentes/paginas/PaginaLogin.tsx`.
  - Protección de rutas en `frontend/src/App.tsx` (redirect a `/login` si no hay sesión).
  - Integración de proveedor auth en `frontend/src/main.tsx`.
  - Servicio de sesión en `frontend/src/servicios/auth.ts` y tipos en `frontend/src/tipos/auth.ts`.
  - Cliente API actualizado con `Authorization: Bearer`, refresh automático en 401 y limpieza de sesión al fallar refresh (`frontend/src/servicios/api.ts`).
  - Botón de cierre de sesión en header (`frontend/src/componentes/organismos/Encabezado.tsx`).
- Validaciones frontend ejecutadas:
  - `npm run lint` ✅ (sin errores, warnings legacy de hooks)
  - `npm run build` ✅
- Continuación A2 (auth UX completa):
  - `PaginaLogin` ahora soporta login, registro, solicitar recuperación y reset de contraseña.
  - `AuthContext` expone `register` además de `login/logout`.
  - `frontend/src/servicios/auth.ts` incluye llamadas a `register`, `forgot-password` y `reset-password`.
  - Flujo de recuperación usa `reset_token_dev` únicamente para staging/desarrollo (pendiente correo real).
- Validaciones post-ajuste:
  - `npm run lint` ✅ (sin errores)
  - `npm run build` ✅
- Continuación A2 (storage auth listo para staging/prod):
  - `backend/servicios/auth_store.py` refactorizado con driver configurable `AUTH_STORE_DRIVER`:
    - `sqlite` para desarrollo local.
    - `postgres` para staging/producción.
  - Alta/lectura de usuarios, revocación de tokens y reset tokens soportados en PostgreSQL con creación automática de tablas auth.
  - Variables nuevas documentadas en `backend/.env.example` y `deploy/staging/staging.env.example` (`AUTH_STORE_DRIVER`, `AUTH_SECRET_KEY`, `AUTH_DB_PATH`).
- Validaciones backend ejecutadas:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (6 passed)
- Continuación A2 (recuperación por correo real):
  - Nuevo servicio `backend/servicios/auth_mailer.py` para envío SMTP de recuperación de contraseña.
  - `POST /api/auth/forgot-password` ahora soporta:
    - `AUTH_RESET_EMAIL_MODE=smtp` → envía correo y no expone token.
    - `AUTH_RESET_EMAIL_MODE=dev` → mantiene `reset_token_dev` para desarrollo.
  - Variables SMTP/documentación añadidas en `backend/.env.example` y `deploy/staging/staging.env.example`.
  - Test nuevo para modo SMTP en `backend/tests/api/test_auth_endpoints.py`.
- Validaciones backend post-correo:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (7 passed)
- Se añadió checklist operativo de cierre A2 en staging:
  - `docs/checklists/CIERRE_A2_STAGING_SMTP.md` (config env, smoke API, forgot/reset SMTP y criterios de cierre).
- Ruta rápida de SMTP implementada para staging:
  - `deploy/staging/docker-compose.yml` incluye servicio `mailhog` (relay SMTP local + bandeja web).
  - `deploy/staging/staging.env.example` actualizado con configuración rápida MailHog (`AUTH_SMTP_HOST=mailhog`, `AUTH_SMTP_PORT=1025`, `STAGING_SMTP_UI_PORT=18025`).
  - Checklist A2 actualizado para contemplar opción rápida local sin proveedor externo.
- Validación E2E en staging desplegado:
  - Backend saludable en `http://localhost:18000/salud`.
  - Forgot-password en modo SMTP sin `reset_token_dev`.
  - Correo recibido en MailHog (`http://localhost:18025`), token recuperado, reset exitoso y login con nueva contraseña OK.
  - Bloque A2 marcado como CERRADO en `docs/arquitectura/ESTADO_PROYECTO.md`.
- Inicio de A3 (contrato canónico + deprecación legacy) sobre Auth API:
  - `backend/api/rutas_auth.py` ahora soporta `?version=v2|legacy` (default `legacy` para compatibilidad temporal).
  - Respuesta `v2` normalizada en envelope canónico: `{ ok, data, meta }`.
  - Respuesta `legacy` mantiene formato previo + headers de deprecación (`Deprecation`, `Sunset`, `Link`).
  - Telemetría de uso de contrato auth agregada en `backend/data/auth_contract_usage.json`.
  - Tests nuevos para contrato v2 y deprecación legacy en `backend/tests/api/test_auth_endpoints.py`.
- Validaciones backend post-A3(auth):
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (9 passed)
- A3 (fase 2): frontend auth migrado a contrato canónico v2
  - `frontend/src/servicios/auth.ts` ahora consume `?version=v2` en `login/register/me/refresh/logout/forgot/reset`.
  - Normalización de respuesta para soportar envelope v2 (`{ok,data,meta}`) con fallback legacy.
  - `frontend/src/servicios/api.ts` refresco de token actualizado a `/api/auth/refresh?version=v2` y parseo de envelope v2.
- Validaciones A3 fase 2:
  - `npm run lint` ✅ (sin errores; warnings legacy de hooks)
  - `npm run build` ✅
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py` ✅ (6 passed)
- A3 (fase 3): contrato v2 pasa a default en Auth API
  - `backend/api/rutas_auth.py` ahora usa `version=v2` por defecto en endpoints auth.
  - Legacy queda disponible solo por pedido explícito (`?version=legacy`) con headers de deprecación.
  - Suite de tests auth actualizada para cubrir ambos flujos (default v2 + legacy explícito).
- Validaciones A3 fase 3:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (10 passed)
- A3 (fase 4): telemetría operable de adopción de contrato en Auth API
  - Nuevo endpoint `GET /api/auth/contract-usage?days=7` para consultar uso `v2` vs `legacy` por fecha y resumen.
  - Se reutiliza almacenamiento local de telemetría (`backend/data/auth_contract_usage.json`) ya presente en auth.
  - Test añadido para validar resumen de métricas de contrato.
- Validaciones A3 fase 4:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (11 passed)
- A3 (fase 5): inicio de contrato canónico v2 en Bitácora
  - `backend/api/rutas_bitacora.py` agrega `?version=v2|legacy` en endpoints `GET /api/bitacora` y `GET /api/bitacora/resumen`.
  - Legacy se mantiene por defecto temporal con headers de deprecación (`Deprecation`, `Sunset`, `Link`) para compatibilidad controlada.
  - Se habilita telemetría de adopción para Bitácora con `GET /api/bitacora/contract-usage?days=7`.
  - Tests nuevos de contrato en `backend/tests/api/test_bitacora_contract.py`.
- Validaciones A3 fase 5:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_bitacora_contract.py backend/tests/test_rutas_bitacora_payload.py backend/tests/test_smoke_api.py` ✅ (6 passed)
- A3 (fase 6): ampliación de contrato canónico en Bitácora para endpoints analíticos
  - `GET /api/bitacora/estadisticas` y `GET /api/bitacora/metricas` ahora soportan `?version=v2|legacy`.
  - Legacy mantiene compatibilidad por defecto temporal con headers de deprecación (`Deprecation`, `Sunset`, `Link`).
  - Se reforzaron pruebas de contrato para validar links de migración en `resumen`, `estadisticas` y `metricas`.
- Validaciones A3 fase 6:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_bitacora_contract.py backend/tests/test_rutas_bitacora_payload.py backend/tests/test_smoke_api.py` ✅ (6 passed)
- A3 (fase 7): contrato canónico extendido a endpoints operativos de Bitácora
  - `GET /api/bitacora/{apuesta_id}` ahora soporta `?version=v2|legacy`.
  - `PATCH /api/bitacora/{apuesta_id}/resultado` ahora soporta `?version=v2|legacy`.
  - `DELETE /api/bitacora/{apuesta_id}` ahora soporta `?version=v2|legacy`.
  - En modo legacy se mantienen headers de deprecación (`Deprecation`, `Sunset`, `Link`) con ruta successor precisa por recurso.
  - Pruebas de contrato ampliadas para rutas con `apuesta_id` y endpoint de resultado.
- Validaciones A3 fase 7:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_bitacora_contract.py backend/tests/test_rutas_bitacora_payload.py backend/tests/test_smoke_api.py` ✅ (6 passed)
- A3 (fase 8): contrato canónico en resolución de apuestas fútbol
  - `POST /api/futbol/apuestas/resolver` ahora soporta `?version=v2|legacy`.
  - En `legacy` se exponen headers de deprecación (`Deprecation`, `Sunset`, `Link`) hacia `version=v2`.
  - Se agregó telemetría de adopción para el dominio con `GET /api/futbol/apuestas/contract-usage`.
  - Prueba unitaria nueva para contrato/telemetría: `backend/tests/api/test_apuestas_futbol_contract.py`.
- Se formalizó criterio global de sunset en `docs/arquitectura/ADR-004-sunset-contratos-legacy.md`:
  - retiro de legacy con `<5%` de uso por 7 días corridos + aviso previo de 30 días.
- Inicio de A4 (legal transversal mínimo):
  - Backend auth ahora exige aceptación legal explícita en registro (`accepted_legal=true`) y versión vigente (`legal_version=2026-03-18`).
  - Persistencia por usuario de aceptación legal en `auth_users` (`legal_accepted_version`, `legal_accepted_at`) con compatibilidad SQLite/PostgreSQL.
  - Frontend agrega páginas legales públicas (`/legal/terminos`, `/legal/privacidad`, `/legal/disclaimer`).
  - Formulario de registro exige checkbox de aceptación legal con enlaces directos a documentos legales.
- Validación A4 fase inicial:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅
  - `npm run lint` ✅ (sin errores, warnings legacy)
  - `npm run build` ✅
- A4 (fase 2): regularización legal para usuarios existentes
  - Nuevo endpoint autenticado `POST /api/auth/accept-legal?version=v2|legacy`.
  - Permite registrar aceptación de versión legal vigente para cuentas legacy y persiste `legal_accepted_version` + `legal_accepted_at`.
  - `backend/servicios/auth_store.py` incorpora `actualizar_aceptacion_legal` para SQLite/PostgreSQL.
  - Test añadido: `test_accept_legal_actualiza_version_del_usuario`.
- Validación A4 fase 2:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅ (13 passed)
- Cierre A4 (fase 3): guard legal endurecido en flujos críticos de auth
  - `backend/api/rutas_auth.py` ahora bloquea `login`, `refresh`, `me` y `logout` con `403 LEGAL_REACCEPT_REQUIRED` si `legal_accepted_version` no coincide con `LEGAL_CURRENT_VERSION`.
  - Se mantiene vía de regularización explícita con `POST /api/auth/accept-legal?version=v2`.
  - Test nuevo `test_guard_legal_bloquea_login_si_version_queda_desactualizada` en `backend/tests/api/test_auth_endpoints.py`.
- Validación A4 fase 3:
  - `backend/.venv/bin/python -m pytest -q backend/tests/api/test_auth_endpoints.py backend/tests/test_smoke_api.py` ✅
