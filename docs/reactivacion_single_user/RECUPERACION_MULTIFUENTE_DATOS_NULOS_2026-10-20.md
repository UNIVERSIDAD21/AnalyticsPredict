# Recuperación multi-fuente de estadísticas nulas — 2026-10-20

## Estado vigente

**Recuperación parcial aplicada; la búsqueda continúa y el catálogo de fútbol no está completo.** Los backfills tocaron únicamente seis métricas por partido finalizado: corners FT, disparos totales y tiros al arco, lado local/visitante. No modificaron goles, partidos futuros, apuestas, modelos ni predicciones.

Los `NULL` siguen significando dato desconocido/no publicado, nunca cero. Un valor canónico no nulo no se sobrescribe. Las fuentes con identidad ambigua, discrepancia o derechos/contrato insuficientes quedan excluidas. La cantidad de partidos con nulos no representa una cantidad recuperable.

## Continuidad más reciente — 2026-10-21 01:45 UTC

La transacción Neon `REPEATABLE READ, READ ONLY` de 01:45:25 UTC mantiene 24.593
finales FT y **4.603 partidos con algún NULL / 26.414 celdas**. Por fuente original,
los siete códigos residuales se separan en **97 gaps ESPN_SOCCER** y **4.506
SOFASCORE**. La auditoría previa ESPN cubre exactamente esos 97 gaps: 97/97 summaries
HTTP 200, identidades verificadas y `statistics=[]`; no hay valores ESPN objetivo que
aplicar en esa cohorte.

El ZIP Kaggle MIT de FA Cup/Coppa Italia ya disponible localmente (8.856 filas; temporadas
hasta 2024/25) se cruzó en consulta de solo lectura contra todos los finales canónicos
usando local/visitante ordenados, aliases exactos normalizados y fecha inferida
temporada+`DD.MM` ±1 día. Hubo pares de equipos fuera de fecha (256 filas FA Cup y 431
Coppa Italia), pero **0 identidades dentro de la ventana**, incluso sin usar el código
interno como filtro. No aporta valores nuevos al corte.

Búsqueda adicional de catálogos gratuitos: HF devolvió cuatro listas vacías; Kaggle
respondió con reCAPTCHA, DuckDuckGo con desafío humano y Mojeek con CAPTCHA. Bing no
mostró un candidato exacto útil. Los desafíos se detuvieron sin resolver; el buscador
OpenClaw configurado permanece sin clave y no se cambió. GitHub HTML específico también devolvió cero para FA Cup, Norwegian Cup, Taça da Liga
y stats de copas; el único resultado UEFA cubría una final de 2019. Un repo MIT que
usa `sofascore-wrapper` cubre solo la liga turca y no acredita derechos upstream.
Ninguna de estas búsquedas es prueba de inexistencia global. Sin DDL/DML, credenciales,
nueva descarga o nuevo valor en esta auditoría. Evidencia reproducible
`SOURCE_SPLIT_AND_FREE_CROSSWALK_20261021T014525Z.json`,
`GITHUB_HTML_FREE_SOURCE_SEARCH_20261021T0148Z.json`; script privado externo
`source_split_kaggle_crosswalk_readonly.py`.

## Aplicación confirmada — 2026-10-21 01:27 UTC

Una cohorte gratuita del Kaggle `gokhanergul/football-match-statistics` se examinó
contra el CSV MIT ya presente localmente, scoreboards ESPN archivados y Neon. Para
dos partidos de Coupe de France de 2019 el score del CSV no conciliaba con el FT
canónico, pero sí coincidía con ESPN independiente y la identidad exacta por torneo,
fecha local, equipos ordenados y fila canónica única. Se aplicaron **solo las seis
estadísticas de cada partido**: Nancy–Guingamp (corners 4–7, tiros 14–18, SOT 5–7;
Kaggle/ESPN 1–2, FT canónico 1–1) y Villefranche–PSG (corners 1–9, tiros 6–23,
SOT 0–7; Kaggle/ESPN 0–3, FT canónico 0–0). Los marcadores no se modificaron ni se
adjudicó en este bloque la causa de su diferencia. Trelissac–Marseille fue excluido:
Kaggle y ESPN no coincidían en FT. Los valores fueron aplicados con el archivo original
sin cambio (SHA-256 `a68ff180ca03e5814a2fda19e8f7d9c298bebd4e1914a97eac986ba54c2a0a51`),
procedencia campo-a-campo, respaldo privado, ensayo de escritura y rollback, y postflight
independiente READ ONLY. El primer intento de verificación posterior a la transacción
falló por un `NameError` en el verificador; se corrigió el lector/verificador y no se
repitió el `apply`. La comprobación independiente confirmó 2 partidos, 12 valores,
2 vínculos, 12 observaciones y FT preservados.

Último censo READ ONLY independiente: **2026-10-21 01:27:53 UTC**, 24.593 finales FT,
4.603 partidos con al menos un NULL y 26.414 celdas. Por campo: 4.092 corners local,
4.092 visitante, 4.583 tiros local, 4.583 visitante, 4.532 tiros al arco por lado.
Por competición: ENG_FACUP 862/4.814 celdas; ESP_COPA 338/1.942; EUR_CHAMPIONS
336/1.866; EUR_CONFERENCE 968/5.262; EUR_EUROPA 796/4.746; FRA_COUPE 1.104/6.598;
ITA_COPPA 199/1.186. Los cinco torneos de liga del alcance tienen cero partidos con
gaps en esas seis métricas. Neon registra ahora **236 vínculos, 1.386 valores
NULL-only y 1.398 observaciones**. Conteos y filas de control están en el censo privado
`NEON_CENSUS_READONLY_20261021T012753Z.json`; evidencia adicional y manifiesto en
`FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/`.

El crosswalk de SofaScore/competiciones está mal en al menos dos filas. La ficha oficial
de Norges Fotballforbund confirma Fredrikstad–Molde, 7-dic-2024, como final de la Copa
Noruega (0–0 reglamentario, definición 5–4 en penales), pero el registro está bajo
`ENG_FACUP`. La ficha oficial de Liga Portugal sitúa Sporting CP–CD Nacional 3–1,
29-oct-2024, en la ruta `allianzcup`; el registro está bajo `ITA_COPPA`. SofaScore
IDs 29/327 aún necesitan mapearse a nivel de todo el catálogo. El `pais_id` de los
cuatro equipos es NULL, por lo que el alcance y los países no se pueden inferir de DB.
No se recategorizó ni se modificaron métricas por este hallazgo. El censo por esas
etiquetas no equivale a cobertura verificada de FA Cup/Coppa Italia.

La búsqueda pública específica de datos estadísticos para esas copas/categorías
reclasificables no mostró datasets en Hugging Face, GitLab ni DataCite. GitHub API
respondió 403 por rate limit y Zenodo 403 por restricción de tráfico; se detuvo sin
reintentar ni evadir. El match page oficial noruego no expuso corners, tiros totales
ni SOT. No se descargaron datasets ni se persistieron estadísticas de esas fuentes.
El informe externo `COMPETITION_CROSSWALK_FREE_SOURCE_REVIEW_20261021T0135Z.json`
incluye fuentes, IDs, resultados y hashes. El backfill gratuito no cubre íntegramente
los 4.603 partidos con gaps; el trabajo continúa sin pagos, trials, credenciales
nuevas, scraping prohibido ni inferencias desde NULL.

## Censo de referencia previo — READ ONLY, 2026-10-20 23:59 UTC

- **24.593** partidos finalizados con FT.
- **4.605 partidos** aún tienen al menos un `NULL` en las seis métricas objetivo; suman **26.426 campos nulos**.
- Nulos por campo: corners local **4.094**, corners visitante **4.094**, disparos local **4.585**, disparos visitante **4.585**, tiros al arco local **4.534**, visitante **4.534**.
- Partidos con gaps por competición: ENG_FACUP 862; ENG_PREMIER 0; ESP_COPA 338; ESP_LALIGA 0; EUR_CHAMPIONS 336; EUR_CONFERENCE 968; EUR_EUROPA 796; FRA_COUPE 1.106; FRA_LIGUE1 0; GER_BUNDESLIGA 0; ITA_COPPA 199; ITA_SERIEA 0.
- El desglose transaccional por temporada/campo reconcilia en 53 grupos: ENG_FACUP 7 temporadas/862 partidos/4.814 celdas; ESP_COPA 9/338/1.942; EUR_CHAMPIONS 8/336/1.866; EUR_CONFERENCE 5/968/5.262; EUR_EUROPA 8/796/4.746; FRA_COUPE 8/1.106/6.610; ITA_COPPA 8/199/1.186. Las cinco ligas principales siguen en cero. El detalle de cada temporada y cada campo, sin IDs de partido, está en `CENSO_POR_TEMPORADA_READONLY_20261021.json` de la entrega privada externa.
- Hellas Verona–Roma (2020-09-19) ya no tiene gaps: se completó solo corners local `0`, explícito y concordante en ESPN, HF/API-Football y DataHub; Kaggle CC0 lo corroboró. El FT canónico 3–0 se preservó, aunque ESPN/DataHub/Kaggle reportan 0–0 jugado. La causa de la diferencia de score no se adjudicó en esta auditoría. Los tiros de DataHub/Kaggle discrepan de ESPN/HF y no se cambiaron.

Este censo no afirma que todos los 4.605 partidos sean recuperables. Hay partidos adjudicados/no jugados, temporadas sin publicación y diferencias de definición entre fuentes.

## Lotes persistidos antes de la excepción final y procedencia

| Fuente | Vínculos fuente-partido | Valores nuevos NULL-only | Observaciones registradas |
|---|---:|---:|---:|
| ESPN Soccer | 193 | 1.152 | 1.154 |
| DataHub Football CSV | 4 | 24 | 24 |
| Kaggle `gokhanergul/football-match-statistics` | 31 | 178 | 186 |
| Hugging Face `eatpizzanot/soccer-dataset` | 4 | 19 | 19 |
| **Subtotal de lotes anteriores** | **232** | **1.373** | **1.383** |

El número de observaciones puede superar los valores escritos porque se conservan comprobaciones iguales/conflictivas sin sobrescribir el dato canónico. Los vínculos cuentan cada combinación proveedor-partido, no necesariamente partidos canónicos distintos. Después de la excepción de Verona–Roma se añadieron **2 vínculos** (ESPN y DataHub; se reutilizó el vínculo HF existente), **1 valor canónico** y **3 observaciones**; total actual Neon: **234 vínculos / 1.374 valores / 1.386 observaciones**. El archivo CC0 de `ferrariboy4k/top5leagues` se usó solo como corroboración externa; no se añadió como cuarta fuente persistida porque atribuye los datos a upstreams que ya están representados.

La última tanda DataHub añadió **Almería–Real Betis (2023-02-11)** y **Espanyol–Real Sociedad (2023-02-13)**: 12 valores. Se cruzaron competición, fecha local exacta, orden/localía, FT, alias de proveedor documentados y candidato canónico único. Ambos lados tenían los seis campos `NULL` y la fuente PDDL tenía seis enteros positivos explícitos por partido. Se aplicó backup privado, ensayo transaccional con rollback verificado y postflight transaccional e independiente. Censo: 4.608→4.606 dentro del ensayo, de vuelta a 4.608 tras rollback; aplicación final 4.606. Migración adicional no necesaria.

El historial de tandas ESPN, DataHub, Kaggle y HF —incluyendo hashes, raws disponibles, backups, rollback y postflights— permanece en la entrega externa indicada al final. La tabla de procedencia conserva proveedor, evento, campo, valor, contrato, evidencia de identidad y hash.

En el censo inicial tras DataHub el total fue 4.608→4.606 dentro del ensayo y de vuelta a 4.608 tras rollback; la aplicación de esa tanda dejó 4.606. Después se aplicó la excepción Verona–Roma, y el censo READ ONLY actual bajó a 4.605.

La excepción Verona–Roma tiene auditoría reproducible en `backend/scripts/aplicar_cero_corners_verona_roma.py`: modo READ ONLY predeterminado, identidad exacta y limitada, respaldo externo, ensayo con rollback, UPDATE exclusivo `NULL`-only y postflight independiente. El desacuerdo de score queda en la evidencia; no se utiliza para mutar el FT ni se generaliza a otros cruces.

## Búsqueda multi-fuente realizada

| Fuente | Cobertura/resultado observado | Decisión |
|---|---|---|
| ESPN Soccer | Se inspeccionaron 164/164 scoreboards válidos: 2.695 eventos y 2.687 finales. 75 coincidencias 1:1; 47 summaries aportaron inicialmente 282 observaciones (seis por partido), 28 no incluyeron estadísticas. La ampliación y el cruce de históricos aportaron tandas adicionales; los summaries sin boxscore útil no se reutilizaron como si tuvieran ceros. | Los valores verificados se aplicaron campo-a-campo. El desfase histórico ESPN↔SofaScore se acepta solo para +5 h exactas y mismo día UTC cuando también concilian IDs, lados, competición y FT; no se corrigen fechas canónicas. |
| DataHub Football CSV | Paquete ODC-PDDL 1.0, cinco ligas/40 CSV/14.285 filas. 9.911 identidades iniciales estrictas; el nuevo crosswalk corto de LaLiga descubrió dos filas positivas adicionales. | Los lotes originales aplicaron cuatro partidos/24 valores. Luego corroboró el cero local de Verona–Roma con ESPN y HF; solo ese corner se aplicó, con el 3–0 canónico preservado. Otros desacuerdos no se sobrescribieron. |
| Kaggle `gokhanergul/football-match-statistics` | CSV con partidos de ligas/copas; se conciliaron filas por fecha, competición, orden y FT, incluyendo alias explícitos limitados. Una fila adicional Bordeaux–Jumeaux fue corroborada con páginas de FFF y Girondins. | 31 vínculos y 178 valores; 6 iguales y 2 conflictos se preservaron sin escritura. Los otros 11 candidatos por nombre no identificaban a los equipos canónicos indicados y no se forzó el cruce. |
| Hugging Face `eatpizzanot/soccer-dataset` | Revisión fijada a `f0cbe86bee3f28cc4b803f735a5287968741c471`; el crosswalk encontró ceros dudosos, conflictos y dos lados con tiros internamente imposibles. | Solo 19 valores positivos de 4 partidos superaron los controles; ceros dudosos y lados inconsistentes excluidos. El card declara CC BY 4.0 y atribuye parte de los datos a API-Football/football-data.co.uk, aunque el card advierte que podría no otorgar derechos sobre upstream; se conserva esa limitación. |
| Hugging Face `Sporoseseun/soccer-dataset` | Declara la misma licencia/fuentes/esquema. La comparación de las revisiones fijadas encontró los mismos 17 archivos Git y los mismos 11 OID/tamaños LFS; incluye el mismo parquet de estadísticas. | Duplicado exacto del dataset ya auditado; no se redescargó, no añade cobertura ni se usa como fuente independiente. |
| Kaggle `ferrariboy4k/top5leagues` | CC0 según la ficha; 40 CSV de 5 ligas 2014–2022 con corners, tiros y tiros al arco. En Hellas Verona–Roma 2020-09-19 reporta FT jugado 0–0, 0–6 corners y 9/15 tiros, 7/7 a puerta. La ficha atribuye fuentes a football-data.co.uk, understat, sofifa y transfermarkt. | Se usó como corroboración solo del cero local de corners junto con ESPN/HF/DataHub. Sus tiros no concilian con ESPN/HF y no se aplicaron; no se registró como upstream independiente. |
| Kaggle `gokhanergul/france-and-germany-football-leagues-dataset` | Apache 2.0 declarado; 38.596 partidos en Francia/Alemania, con Coupe de France y DFB-Pokal. Archivo revisado: un CSV, 10 columnas: competición, fecha, equipos, scores y temporada. | No tiene corners, tiros ni tiros al arco. No aplicado; raw ZIP y cabeceras archivados con hash. |
| Kaggle `adamgbor/club-football-match-data-2000-2025` | MIT en la ficha; anuncia datos 2000–2026 de 42 ligas y stats desde Football-Data.co.uk. | No incluye copas según su catálogo/descripción; derechos upstream no verificados. No descargado ni aplicado. |
| Kaggle `sagehaz/Football_Match_Datasets` | MIT en la ficha; CSV semanales 2025 con columnas de resultados/estadísticas, pero el README solo declara la licencia y no identifica fuente/proveedor. | No usado por falta de procedencia verificable de los datos subyacentes. |
| Hugging Face `tarekmasryo/football-matches-2025-dataset` | CC BY 4.0 declarado; 1.941 partidos 2024/25 de cinco ligas + Champions; 23 columnas de resultado/árbitro/fixture, sin las seis métricas objetivo. | No aporta los campos estadísticos faltantes; no descargado. |
| Kaggle `willfitzhugh/european-soccer-data` | La copia declara CC0 y contiene 106.876 filas de partidos/lado, incluidos cups y UEFA; su CSV solo trae fecha, equipos, marcadores, puntos, temporada, ubicación, país y competición. No trae corners, tiros ni tiros al arco. | Descargado y revisado; no sirve para las métricas objetivo. Hash ZIP `2ba6976b571feaa9b294f5e15d799eec39b1673eeeba5df7fcbc95b06934d884`. |
| Kaggle `omarameen99/football-matches-data-from-soccerway` | Declara Apache 2.0, 55 competiciones y 16.688 partidos recientes con estadísticas; su descripción atribuye el dataset a un proceso automatizado Selenium/BeautifulSoup sobre Soccerway. El `robots.txt` público de Soccerway desautoriza `/football/`. | No se descargó ni usó. Extracción upstream sistemática y derechos de redistribución no acreditados; no se eludió la política del sitio. |
| Kaggle `johntocci/champions-league-matches-2025-2026` | Declara CC0, pero describe scraping automatizado diario desde FBref; cubre una temporada UCL y subset de métricas. FBref respondió 403 en auditoría anterior. | No se usó ni se eludió el bloqueo. |
| Kaggle `ivanposinovec/football-matches-from-europe-and-south-america` | Declara CC0, pero el propio card dice que los partidos se obtuvieron scrapeando FBref y exige aceptar Sports Reference Terms of Use. | No descargado ni usado bajo las restricciones actuales de fuente. |
| Wyscout Open Data (copia Kaggle `aleespinosa`) | CC BY 4.0, cinco ligas principales 2017/18 más World Cup 2018 y Euro 2016; no declara las copas de clubes objetivo. Copia de ~3,2 GB. | No cubre las competiciones objetivo restantes según el alcance publicado; no descargado. |
| Kaggle `tonygordonjr` | Atribuye datos a API-Football/RapidAPI y declara uso no comercial/académico. | No utilizado por restricción de uso y derechos upstream no aclarados. |
| StatsBomb Open Data | Licencia declarada CC BY 4.0. El catálogo público actualizado lista 80 combinaciones competición-temporada: Champions League hasta 2018/19, Copa del Rey solo 1977/78–1983/84 y Europa League 1988/89; no lista FA Cup, Coupe de France, Coppa Italia ni Conference League. El cruce estricto previo cubrió 1.819 partidos de 17 listas UCL/ligas y 155 candidatos; ninguno tenía gaps objetivo. | Las temporadas de Copa del Rey/Europa son anteriores al histórico residual; UCL 2018/19 ya fue cruzada sin gaps. Sin nuevos campos recuperables para los NULL examinados. Atribución requerida si se reutiliza; no se descargaron eventos ni se derivaron valores en esta pasada. |
| PitchAPI y football-data.org | PitchAPI documenta estadísticas, pero su endpoint requiere clave y no se verificó cobertura real; football-data.org anuncia corners/tiros como complemento pagado. | No se recibió clave ni se compró plan. |
| FBref, TheSportsDB, football-data.co.uk | Se observaron 403/desafío o timeout en las consultas previas. FFF/UEFA y otros sitios oficiales están sujetos a condiciones de reutilización distintas. | No se sortean bloqueos ni se automatizan sitios cuyos términos lo prohíben. No se atribuyen datos no publicados. |

Un barrido adicional de catálogos Kaggle/Hugging Face/GitHub encontró copias de Adamgbor con upstream Football-Data.co.uk; `WideMan/football_matches` sin licencia declarada y sin cobertura de copas objetivo acreditada; un dataset HF de detección de imágenes; mirrors FBref sin términos claros; y un conjunto reciente francés/alemán que solo contiene marcador, fecha y equipos. No aportan una fuente nueva utilizable. También se confirmó que el mirror HF de Sporoseseun es una copia binaria exacta del dataset HF ya auditado, sin cobertura independiente. No se usaron fuentes con métricas sin upstream/licencia claros. El extractor de búsqueda web configurado no tuvo clave; no se alteró Gateway ni se intentó eludir ese requisito.

## Búsqueda API complementaria — 2026-10-20, hallazgos históricos (no candidatos vigentes)

Una herramienta de búsqueda web independiente permitió comprobar documentación oficial y endpoints demo sin cuentas personales, compras ni credenciales del proyecto. Evidencia agregada, sin copiar filas de partidos, en `APIS_HISTORICAS_COPAS_Y_UEFA_20261020.json` de la entrega privada externa.

| API | Hecho comprobado | Resultado para los gaps actuales |
|---|---|---|
| FootyStats | `league-list` con clave demo respondió 1.738 entradas y enumera las siete competiciones residuales; la documentación incluye corners, disparos y tiros al arco. El demo solo acreditó EPL 2018/19 (380/380) y devolvió HTTP 417 para las siete muestras 2024/25 objetivo; el catálogo **no demuestra cobertura estadística** de los gaps. | **Excluida por el filtro gratuito vigente:** el acceso gratuito utilizable no cubre las copas objetivo; los términos restringen automatización y el resto no se considera. No se consultaron páginas de partidos ni se descargaron CSV. Referencias solo para documentar el descarte: [catálogo](https://footystats.org/api/documentations/league-list), [partidos y stats](https://footystats.org/api/documentations/match-schedule-and-stats), [términos API](https://footystats.org/api/documentations/terms-of-use-and-legal). |
| API-Football / API-Sports | La documentación pública declara estadísticas y temporadas gratuitas limitadas; la disponibilidad varía por competición/temporada y no se pudo comprobar el historial residual. Sus términos no acreditan permiso para publicar en el producto y reservan derechos a ligas/organizadores. | **Excluida:** no se puede demostrar cobertura gratuita por los partidos/campos residuales ni los derechos de uso requeridos. No se creó cuenta/clave ni se consultaron stats autenticadas. [Cobertura](https://www.api-football.com/coverage), [términos](https://www.api-football.com/terms). |
| Football Soccer API | Declara estadísticas de corners/disparos y archivo histórico; el endpoint de stats requiere el plan Archive. Sus términos prohíben descarga masiva para reconstruir una base de datos y redistribuir/publicar los datos. | Excluida para el backfill multijuego de la base canónica. Fuentes: [stats](https://footballsoccerapi.com/documentation/match-statistics), [histórico](https://footballsoccerapi.com/documentation/historical-data), [términos](https://footballsoccerapi.com/terms). |
| Stats API | Su documentación declara stats por partido y fuente upstream, pero el catálogo detallado requiere autenticación; la ruta pública de cobertura respondió 401. | **Excluida:** sin datos verificables gratuitamente y con términos que limitan almacenamiento masivo. No se abrió cuenta ni se hizo una petición autenticada. [Cobertura](https://stats-api.com/coverage), [fuentes](https://stats-api.com/data-sources), [términos](https://stats-api.com/legal/terms), [uso aceptable](https://stats-api.com/legal/acceptable-use), [contrato](https://stats-api.com/docs/endpoints/matches). |
| Big Balls Sports Data | Publica UCL 2025/26 y 2026/27 para scores/matches; esa ficha no lista endpoint de estadísticas de equipos para esas temporadas. | No sustituye estadísticas históricas de copa/UEFA. [Cobertura publicada](https://bigballsdata.com/coverage). |
| Footballdata.io | La ruta de estadísticas requiere autenticación; no se halló cobertura pública por fixture/temporada para el residual y sus términos dejan incierto el almacenamiento prolongado/masivo. | **Excluida:** la cobertura y permisos de persistencia no están acreditados en acceso gratuito público. No hubo cuenta, clave ni petición autenticada. [Stats](https://footballdata.io/documentation/matches/), [términos](https://footballdata.io/terms/). |
| Footiqo | Sus páginas muestran estadísticas de corners, shots, shots on target y exportación CSV/Excel filtrada. La navegación incluye Champions, Europa y Conference, no las copas nacionales. La muestra pública revisada es PL 2025/26; cobertura histórica fixture/temporada no comprobada. | Posible vía **manual gratuita y solo UEFA**, aún sin cobertura demostrada; no resuelve las copas nacionales ni habilita automatización. No se pidió export por requerir email/consentimiento de marketing; no se descargó dato. [Base](https://footiqo.com/database/), [datasets](https://footiqo.com/free-football-datasets/), [licencia/política](https://footiqo.com/dataset-licence/). |
| `jokecamp/FootballData` | El README enumera un conjunto heterogéneo con varias fuentes upstream, entre ellas Football-Data.co.uk; la licencia MIT cubre el repositorio, no acredita por sí sola derechos sobre las estadísticas upstream ni cobertura de las copas objetivo. | No descargar/usar como fuente independiente sin procedencia por archivo, temporadas/campos y derechos acreditados. [README](https://github.com/jokecamp/FootballData), [licencia del repo](https://github.com/jokecamp/FootballData/blob/master/LICENSE). |
| `Avinash308/Acad_gild_Machine_Learning_Project2` | El README anuncia ~25.000 partidos de ligas principales de 11 países europeos, 2008–2016, con eventos/estadísticas; la metadata GitHub no reconoce licencia. | Aun si los campos existen, no cubre las temporadas ni las copas/UEFA residuales; no descargado. [Repositorio](https://github.com/Avinash308/Acad_gild_Machine_Learning_Project2). |
| `userchrispo/Soccer-Analyzer` | Descripción del repo anuncia Premier League 2010–2021 y corners/SOT; README solo documenta una clasificación por goles/victorias y no confirma el schema; no hay licencia reconocida. | No cubre las competiciones objetivo, ni se verificaron sus campos/derechos; CSV no descargado. [Repositorio](https://github.com/userchrispo/Soccer-Analyzer). |

Seis búsquedas de repositorios GitHub enfocadas en Champions, Coupe de France, FA Cup, Copa del Rey, Coppa Italia y Conference devolvieron cero resultados cada una. La consulta específica de Europa League fue HTTP 403 por rate limit y no se reintentó. Consultas generales sí encontraron los dos candidatos descritos arriba, descartados por licencia/cobertura. Ningún resultado prueba que no existan otros conjuntos. Resumen de URLs/HTTP en `FOOTBALLDATA_IO_PUBLIC_CONTRACT_20261020/audit_summary.json`.

### Footiqo: candidato de exportación manual para UEFA

La página de base histórica anuncia exportación CSV/Excel de tablas filtradas. La política del 8-oct-2026 permite descargar manualmente por la interfaz normal y retener localmente para investigación personal no comercial, DB privada, análisis, backtesting y experimentos ML; prohíbe scraping, descargas automatizadas y extracción masiva automatizada, aun a baja frecuencia. Conserva salvedades de derechos de terceros y cobertura variable. La navegación pública muestra Champions, Europa y Conference, no FA Cup, Copa del Rey, Coupe de France o Coppa Italia.

El censo agregado READ ONLY de 23:59:12 UTC contiene 21 grupos temporada UEFA con **2.100 partidos** que tienen algún gap y **11.874 celdas NULL**; son una lista de trabajo, no cobertura confirmada del proveedor. No se obtuvo ni descargó estadística alguna en esta pasada. Guía para exportar manualmente las temporadas que la web ofrezca y evidencia legal/catálogo en `FOOTIQO_MANUAL_EXPORTS_20261020/`; la carpeta privada `FOOTIQO_MANUAL_EXPORTS/` está preparada para archivos legítimamente exportados. No automatizar el sitio ni tratar campos ausentes como cero.

La comprobación del almacén protegido y de nombres de variables no encontró `FOOTYSTATS_API_KEY`, `APIFOOTBALL_API_KEY`, `APISPORTS_API_KEY` ni `STATS_API_KEY`. Una solicitud enmascarada de clave gratuita de API-Football venció sin respuesta y no se recibió credencial. No se creó una cuenta, no se pagó un plan y ningún valor de clave fue expuesto ni enviado a terceros.

## Sportmonks y catálogos de datasets — 2026-10-20 Bogotá / 2026-10-21 UTC

Sportmonks es un nuevo lead contractual, no una fuente ya validada para backfill. Su documentación oficial describe estadísticas por fixture (`include=statistics`) con tipos para corners y tiros; los términos permiten almacenar los datos del API y prohíben la reventa directa. La página pública de cobertura lista UCL, Europa League y Conference, pero una cobertura global o una estadística de ejemplo no acredita que exista para cada partido y temporada del proyecto. Los planes base dan acceso a las tres temporadas recientes de cada liga suscrita; el histórico anterior requiere un add-on y solo expone profundidad que el proveedor tenga, que varía por liga/estadística. Se anuncian Starter €29/5 ligas, Growth €99/30, Pro €249/120; el add-on histórico tiene precio único según plan. También se anuncia una opción gratuita sin tarjeta, pero el Coverage Finder exige cuenta. El trial de pago requiere tarjeta y puede facturarse automáticamente si no se cancela. No se creó cuenta, no se solicitó ni usó API key, no se abrió trial, no hubo llamadas autenticadas ni cambios DDL/DML. Antes de incorporar esta vía hace falta verificar, con acceso autorizado, competiciones exactas, temporadas y `type_id` presentes por fixture, además de los derechos aplicables al producto.

En consultas directas de metadatos de Hugging Face, los candidatos nuevos fueron de top-5 —donde no quedan nulos en los seis campos—, video/robótica, o datasets aislados/limitados sin cobertura de copas residuales; no se obtuvo un nuevo dataset histórico reutilizable. El repositorio `ddzyx/european-football-matches-top5` declara CC BY 4.0, pero es top-5. El resultado UCL 2025/26 de SkillCorner declara CC BY-NC 4.0 y no demuestra los campos/fixtures faltantes; no se usa. GitHub devolvió un app de análisis y un análisis de partido individual, no un archivo histórico adicional. Los endpoints públicos de búsqueda de Kaggle respondieron con challenge/verificación de navegador; se detuvo sin cookies, fingerprinting ni bypass. No se descargaron esos resultados.

La evidencia de páginas oficiales de Sportmonks y búsquedas de catálogos, junto con su hash, queda fuera del repositorio en `SPORTMONKS_SOURCE_AUDIT_2026-10-20/`. El censo vigente no cambió: 4.605 partidos y 26.426 campos con NULL; el residuo sigue concentrado en ENG_FA Cup, Copa del Rey, Coupe de France, Coppa Italia y fases/temporadas UEFA.

### Otros leads API: StatPal y Goalserve

StatPal (el sitio legado SoccerDataAPI redirige a este servicio) anuncia estadísticas detalladas con corners y tiros, temporadas/datos históricos y 1.000+ ligas; el marketing legado hablaba de hasta siete años, mientras el sitio actual no fija un rango exacto. La página ofrece un demo público de datos en vivo sin signup y planes desde USD 19/mes con una prueba de 14 días, pero no revela en la muestra una matriz exacta de copas, años, fixtures y tipos estadísticos. La documentación extraída solo expuso la portada v2.0.0. La ruta pública `/terms-of-service/` respondió 404 y no se verificaron derechos de almacenamiento/producto. No se usó el demo, no se creó cuenta ni se empezó prueba.

Goalserve anuncia más de 400 ligas en cobertura live, más de 50 para estadísticas históricas y feeds XML/JSON con resultados, estadísticas e histórico. La prueba gratuita dirige a un formulario de contacto; las páginas públicas revisadas no acreditan las siete competiciones, temporadas históricas, métricas exactas ni precio/condiciones de conservación. No se contactó, registró cuenta, empezó trial ni realizó llamadas.

La portada de Scorebing y la documentación pública de API-Football devolvieron HTTP 403; no se reintentaron ni sortearon. Evidencia y timestamps quedan en `SPORTMONKS_SOURCE_AUDIT_2026-10-20/API_LEADS_STATPAL_GOALSERVE.json`; estos proveedores se mantienen como leads condicionados, no como datos disponibles. El censo no cambia.

### Descarte explícito de FotMob/xValue

Una búsqueda de código en GitHub halló `vsntll/xValue`, cuyo README afirma cubrir copas de clubes de las cinco ligas grandes durante 2020/21–2026/27 y describe scripts que consultan FotMob para boxscores (incl. SOT) y estadísticas de copas. La ficha API pública de GitHub devuelve `license: null` y el path `LICENSE` no existe. No se clonó el repo, no se descargaron sus `data/processed` ni se ejecutó su código.

La fuente original, FotMob, establece en sus términos que los servicios automáticos (robots/crawlers/indexación) y otros métodos de uso sistemático o regular no están permitidos. Su `robots.txt` desautoriza `/api/*` para `User-agent: *` (con excepciones explícitas para algunos search bots). Por tanto, no se replica el API/scraper ni se usa el dataset del repo como upstream licenciado. Este candidato se descarta aunque su README mencione las competiciones/campos.

Evidencia con hashes: `SPORTMONKS_SOURCE_AUDIT_2026-10-20/FOTMOB_XVALUE_EXCLUSION.json`. No hubo petición a endpoints de partidos, DDL/DML ni cambio del censo.

## Cobertura StatsBomb y lead Stats API — 2026-10-20 23:54 UTC

Se actualizó `data/competitions.json` del repositorio público de StatsBomb Open Data y se contaron 80 combinaciones competición-temporada. Las únicas competiciones objetivo listadas son Champions League (18 temporadas, última 2018/19), Copa del Rey (1977/78, 1982/83 y 1983/84) y UEFA Europa League (1988/89). No aparecen FA Cup, Coupe de France, Coppa Italia ni Conference League. La lista confirma que StatsBomb no cubre los huecos clasificatorios UEFA actuales; el cruce exacto previo de UCL ya había hallado cero gaps en 155 candidatos. No se descargaron archivos de eventos ni se añadieron estadísticas.

Stats API es un lead verificable en documentación, no una fuente usable aún. El endpoint de cobertura exige Bearer API key y sin ella devuelve `401 invalid_api_key`. La oferta pública describe 200 solicitudes únicas para nuevas cuentas (30/min, sin tarjeta), mientras Starter aparece a USD 19,50/mes con renovación recurrente después de una prueba aplicable; no se creó cuenta ni se aceptó un trial. El proveedor declara un acuerdo de redistribución API-Football y autoriza usos en productos propios/análisis internos sujetos al plan, pero la política prohíbe espejos masivos; no se puede concluir que un backfill persistente de miles de partidos para esta base/modelo esté autorizado. No se leyó ni persistió ningún payload de estadísticas.

La ejecución queda sin nuevas escrituras en Neon: censo READ ONLY 23:59:12 UTC, **4.605/24.593** finales con algún NULL (26.426 celdas), 234 vínculos y 1.386 observaciones. Evidencia privada: `STATSBOMB_COVERAGE_20261020/`, `STATS_API_PUBLIC_CONTRACT_20261020/` y `CENSO_POR_TEMPORADA_READONLY_20261021.json` bajo la entrega externa `RECUPERACION_MULTIFUENTE_SEGUIMIENTO_2026-10-20/`; el manifiesto SHA-256 cubre todos.

## Cotejo por fase UEFA 2025/26 — READ ONLY, 2026-10-20 23:43 UTC

Un censo por mes UTC acotado a UEFA Champions, Europa y Conference muestra que los partidos de liga principal desde septiembre no tienen gaps estadísticos en esa ventana. Los gaps del calendario 2025/26 se concentran en clasificatorias de julio/agosto:

| Competición | Finales examinados | Con algún gap | Julio 2025 | Agosto 2025 | Meses posteriores con finales |
|---|---:|---:|---:|---:|---|
| Champions League | 281 | 55 | 48 | 7 | 0 gaps |
| Europa League | 271 | 58 | 32 | 26 | 0 gaps |
| Conference League | 409 | 181 | 129 | 52 | 0 gaps |

Los 55 candidatos UCL tienen los seis campos objetivo `NULL` y ninguno cuenta con vínculo en `partidos_fuente_espn_futbol`. ESPN Soccer Scoreboard consultado por los meses julio/agosto y por dos fechas de muestra respondió HTTP 200, pero con cero eventos; no hay IDs ESPN para recuperar por ese endpoint esos clasificatorios. En cambio, un resumen ESPN de la fase principal (Athletic Club–Arsenal, evento 757653, 16-sep-2025) sí ofrece corners/tiros/SOT para ambos equipos y concilia con un único registro canónico que ya tenía esos valores. Esto confirma disponibilidad por fase, no resuelve el residual clasificatorio ni constituye una fuente independiente.

El repositorio público `yanz026/champions-league-2025-26-eda` se usó únicamente para descubrir el ID de un partido; la licencia MIT declarada para el repositorio no acredita derechos sobre estadísticas upstream de ESPN/UEFA y no se importó ningún dato de ese repositorio. Se excluyó TotalCorner porque sus términos, sección 4(e), prohíben extracción automatizada sin autorización escrita. Se excluyó FCStats porque su `robots.txt` desautoriza explícitamente a GPTBot/ChatGPT-User/OAI-SearchBot y la raíz devolvió HTTP 403; no se consultaron páginas de partidos.

El censo global READ ONLY de las 23:43:14 UTC quedó sin cambios frente al anterior: 24.593 finales FT, 4.605 con algún NULL (26.426 campos), 234 vínculos y 1.386 observaciones. No hubo DDL/DML ni nuevas métricas aplicadas. Evidencia resumida y hashes en `UCL_2025_26_ESPN/UEFA_QUALIFYING_PHASE_SOURCE_AUDIT_20261020.json` dentro de la entrega externa.

## Código y operación

- `backend/servicios/resolucion_multifuente_futbol.py`: validación de eventos/identidad, extracción por campo y proveedor, hash, consistencia y merge que conserva valores no nulos. La regla general de hora no se relajó; la excepción +5 h está limitada al importador SofaScore y ESPN en el mismo día UTC.
- `backend/servicios/proveedor_pitchapi.py`: cliente documentado, GET y errores sanitizados; no se usó sin API key.
- `backend/migrations/2026-10-20_observaciones_multifuente_futbol.sql` y allowlists de `DATAHUB_FOOTBALL_DATA`, `KAGGLE_GOKHANERGUL` y `HF_EATPIZZANOT`: la tabla y constraints necesarios existen en Neon y la procedencia de las tandas aplicadas está registrada.
- Scripts de auditoría/aplicación por proveedor en `backend/scripts/`; modo de solo lectura por defecto cuando corresponde, DML explícito, guardas `IS NULL`, lock, backup externo, rollback y postflight.
- No se reentrenó ni activó modelo, no se modificaron apuestas/predicciones, no se creó cron, no se contrató proveedor y no se automatizaron fuentes futuras.

La revisión vigente compiló el resolutor y el script Verona–Roma con `py_compile`, y pasó `git diff --check`. La ejecución predeterminada del script produjo `READ_ONLY_PREFLIGHT_OK`, confirmó el target corner `0`, el FT canónico `3–0`, la identidad y las tres observaciones existentes, con `database_changes=false`; evidencia en `VERONA_ROMA_CORNERS_ZERO/RUN_20261020T231726198596Z/`. Un recenso READ ONLY independiente de Neon confirmó 24.593 finales, 4.605 con gaps (26.426 campos), 234 vínculos y 1.386 observaciones; detalle por competición/campo en `CENSO_READONLY_CIERRE_20261020T231929Z.json`. Un recenso posterior 23:43:14 UTC y el análisis por mes de UEFA están archivados en `UCL_2025_26_ESPN/`. No se ejecutó la suite local en esta pasada y el resultado de pruebas del checkpoint anterior no se presenta como validación de este cambio.

## Continuidad

Se sigue buscando una vía autorizada para copas nacionales y clasificatorias UEFA. Footiqo es una vía potencial **solo para UEFA mediante exportación manual**: sus términos permiten uso privado no comercial en DB/modelos de archivos exportados manualmente por la interfaz, pero prohíben extracción automatizada; la cobertura por temporada/match no se validó y su catálogo público no muestra copas nacionales. Se preparó una matriz de 21 grupos UEFA (2.100 partidos/11.874 celdas con gap potenciales, no cobertura confirmada). Stats API requiere clave y prohíbe espejo masivo; falta resolver cobertura/derechos. FootyStats lista copas pero su demo no las incluye y el plan gratuito es Premier League; API-Football no permite certificar temporadas free ni licencias. StatsBomb no amplía el residual. El censo READ ONLY de 2026-10-20 23:59:12 UTC confirma **4.605/24.593** finales con algún `NULL` (26.426 celdas), 234 vínculos y 1.386 observaciones. No hay fuente validada para todo el catálogo ni ETA confiable. Mantener `NULL` sin evidencia y no declarar datos completos.

Evidencia privada externa: `/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/RECUPERACION_MULTIFUENTE_SEGUIMIENTO_2026-10-20/`, en particular `CENSO_Y_FUENTES_ALTERNATIVAS_20261020T2257Z.json`, `CENSO_READONLY_CIERRE_20261020T231929Z.json`, `UCL_2025_26_ESPN/` (censo actual, candidatos canónicos privados, matriz por temporada/mes, scoreboards ESPN y políticas de fuentes), `STATSBOMB_COVERAGE_20261020/`, `STATS_API_PUBLIC_CONTRACT_20261020/`, `DATAHUB_LALIGA_RESIDUAL_CROSSWALK/application_result.json`, `VERONA_ROMA_CORNERS_ZERO/` (incluye aplicación y preflight READ ONLY posterior), `KAGGLE_CC0_TOP5_PROBE/`, `KAGGLE_GOKHANERGUL_FRANCE_GERMANY_NO_STATS_PROBE/`, `FUENTES_COPAS_BUSQUEDA_SUPLEMENTARIA_20261020.json`, `CATALOGOS_HF_KAGGLE_ADICIONALES_20261020.json`, `APIS_HISTORICAS_COPAS_Y_UEFA_20261020.json`, `NOTA_CONTINUIDAD_APIS_20261020.md` y `MANIFIESTO_SHA256.txt`. La evidencia permanece fuera del repositorio y no incluye secretos.

## Filtro gratuito solicitado por el propietario — 2026-10-21

El propietario aclaró que no autoriza considerar compras ni trials que puedan convertirse en cargos: para continuar solo sirven fuentes gratis, con acceso sin tarjeta/cobro, derechos de uso compatibles y cobertura real por competencia/temporada/métrica. Las opciones con precio descritas en secciones anteriores son exclusivamente contexto de descarte; no son recomendación ni autorización de gasto.

- **FootyStats:** sus páginas públicas enumeran CSV por temporadas en FA Cup, Copa del Rey, Coupe de France y UCL, pero el único sample que anuncia sin registro es EPL 2018/19; la página dirige la descarga programática a su API y el sitio vende créditos CSV. Los términos prohíben acceso no humano/extracción automatizada del sitio y limitan el contenido descargado a uso personal no comercial. Excluido; no se descargaron CSV ni se consultaron páginas de partidos. Fuentes: [FA Cup CSV](https://footystats.org/england/fa-cup/datasets), [Copa del Rey CSV](https://footystats.org/spain/copa-del-rey/datasets), [Coupe de France CSV](https://footystats.org/france/coupe-de-france/datasets), [términos](https://footystats.org/terms-and-conditions), [créditos CSV](https://footystats.org/buy-csv-credits).
- **StrikerAPI:** declara 500 créditos gratis por mes sin tarjeta, exige cuenta y verificación de email; permite almacenar, derivar y usar datos para research/model training mientras se siguen las restricciones del upstream. Su página declara datos públicos ESPN; enumera UCL/UEL/UECL, pero no FA Cup, Copa del Rey, Coupe de France o Coppa Italia. La ficha UCL advierte que las rondas clasificatorias son escasas y mayormente carecen de boxscores; desde 2020/21 la cobertura ESPN que publica queda en fase principal y eliminatorias. Los gaps observados en UEFA 2025/26 están justamente en clasificatorias; no se demostró recuperación fixture/campo y no cubre el residuo nacional. No se creó cuenta, no se solicitó clave ni se hizo llamada. Fuentes: [términos y free credits](https://strikerapi.com/terms), [datos/upstreams](https://strikerapi.com/data), [cobertura UCL](https://strikerapi.com/champions-league).
- **Repos/datasets libres adicionales:** `olbaudayo/open-matchday` anuncia fixtures/resultados/HT/goles, no corners/tiros/SOT, y no declara licencia GitHub; `Ashborn-047/topbin` declara CC0 y recopila marcadores/fixtures de OpenFootball, no las seis métricas; `yanivohayon1/ucl-2021-22` no declara licencia, su visor falla por columnas de CSV incompatibles y ofrece estadísticas a nivel jugador para una sola temporada. `olbauday/FPL-Core-Insights` declara partidos y estadísticas manuales “Opta-like”, pero la API metadata de GitHub da `license:null`; su fuente publicada es ESPN y la fase principal UEFA 2025/26 ya tiene los seis campos completos. No se descargaron datasets ni se usaron esas observaciones.
- **Duplicados/procedencia:** `svgwvgs/soccer-dataset` declara ser un mirror del conjunto HF ya auditado y replica `API-Football + football-data.co.uk`; no es fuente independiente ni añade cobertura al crosswalk existente. `xgabora/Club-Football-Match-Data` trae métricas de liga desde Football-Data.co.uk, sin copas objetivo y sin derechos upstream independientes acreditados. No se copiaron archivos.

No hay fuente totalmente gratuita y validada que cubra todos los gaps restantes. No se abrió cuenta, prueba, API key, contacto, descarga protegida, pago o llamada autenticada; no hubo nueva consulta, DDL/DML ni valores nuevos en Neon. El censo vigente sigue siendo el READ ONLY 2026-10-20 23:59:12 UTC: 4.605/24.593 partidos con NULL y 26.426 celdas; recuperación parcial guardada: 234 vínculos, 1.374 valores y 1.386 observaciones. La búsqueda sigue abierta y no se declara completitud. Evidencia externa privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

## Catálogo gratuito ampliado — 2026-10-21

Una búsqueda pública por competición consultó metadatos de Kaggle/Hugging Face, Zenodo y los índices OpenFootball; no se descargaron archivos deportivos. El mejor candidato aparente fue `ivanposinovec/football-matches-from-europe-and-south-america` (Kaggle lo etiqueta CC0): declara 27.000+ reportes, partidos de copas nacionales en rondas con clubes de primera división y UCL/UEL/Conference entre 2015 y 2023. Pero la misma ficha dice que el dataset fue scrapeado de FBref y que su uso implica aceptar los términos de Sports Reference. No se asumió que la etiqueta CC0 del repositorio anule ese requisito; queda excluido hasta existir autorización clara. Otro dataset (`ramostherunning/champions-league-historical-match-20202026`) describe 1.383 partidos, incluidas clasificatorias UCL y corners/tiros/SOT, pero su etiqueta de licencia es “Other” y no declara fuente/upstream ni permiso persistente, así que tampoco se usa. El dataset Wyscout de Figshare/Kaggle con CC BY 4.0 parece cercano por el título, pero su detalle de alcance son cinco ligas de 2017/18 más Mundial 2018/Euro 2016; no incluye copas nacionales ni torneos de clubes UEFA residuales y los archivos rondan 3,23 GB, así que no se descargó. Los otros resultados CC0 eran agregados por temporada, un EFL Cup fuera de las 12 competiciones objetivo, tiros a puerta sin tiros totales/corners o fixtures/resultados sin stats. Zenodo devolvió resultados top-5/non-commercial o artículos, no un dataset elegible para las copas residuales. No hay valores nuevos en esta búsqueda. Fuente: [Kaggle Ivan Posinovec](https://www.kaggle.com/datasets/ivanposinovec/football-matches-from-europe-and-south-america), [Kaggle UCL 2020–26](https://www.kaggle.com/datasets/ramostherunning/champions-league-historical-match-20202026), [Wyscout CC BY 4.0](https://www.kaggle.com/datasets/aleespinosa/soccer-match-event-dataset), [índice abierto](https://github.com/withqwerty/open-football). Evidencia privada: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

## Búsqueda de catálogos GitHub/Hugging Face/Zenodo — 2026-10-20

Una revisión adicional de metadatos no encontró fuente nueva elegible. `xgabora/Club-Football-Match-Data` anuncia 238.858 partidos y 38 códigos de liga/división hasta septiembre de 2026; el README atribuye los resultados/estadísticas a Football-Data.co.uk y Elo a ClubElo. La licencia MIT publicada pertenece al repositorio, pero no se encontró una declaración independiente que autorice reutilizar el dataset upstream y el esquema descrito cubre ligas, no copas nacionales o clasificatorias UEFA. No se descargaron sus CSV de 45 MB/11 MB ni se incorporaron observaciones.

En Hugging Face, el dataset `julien-c/kaggle-hugomathien-soccer` declara ODbL y partidos/eventos de ligas, sin cobertura acreditada de las competiciones residuales ni conciliación de los seis campos; `Damir81/football-charts-results-goal-timing` (CC BY 4.0) contiene resultados y minutos de gol, no stats objetivo. Otros candidatos eran EPL/top-5, un dataset UEFA 2025/26 con CC BY-NC 4.0, o carecían de licencia/origen suficiente. Zenodo devolvió principalmente publicaciones, ligas top-5 y resultados/goal timing; el registro `10.5281/zenodo.10120708` es solo 2022/23 Big Five y CC BY-NC-ND 2.0. Ningún archivo adicional fue descargado.

La búsqueda se limitó a APIs públicas de metadatos de GitHub, Hugging Face y Zenodo; no se sortearon desafíos/bloqueos. Un candidato de Hugging Face contiene una muestra gratuita de 20 partidos de 18 competiciones internacionales. El README declara 29 métricas de equipo, incl. `Shots_On_Target` y `Corners`; en la muestra, de 10 filas UEFA (5 partidos), `Corners` y `Goal_Attempts` aparecen en 10/10, SOT y tiros fuera en 6/10 y tiros bloqueados en 8/10. No existe columna `Shots_Total` y `Goal_Attempts` no tiene equivalencia documentada, por lo que no se infiere tiros totales. La muestra no aportó nuevos valores. La oferta ampliada, de pago, queda excluida por la instrucción gratuita vigente; cubre solo parte de UEFA y no copas nacionales ni la mayoría de clasificatorias. No se adquirió ningún producto.

La muestra se descargó temporalmente a memoria para evaluación y no se persistió ni se incorporó al producto. Cruce READ ONLY: 5 partidos de UCL/UEL/Conference; 2 registros canónicos únicos dentro de ±1 día y ambos ya tenían las seis métricas llenas (Atlético Madrid–Real Madrid 2025-03-12 y HNK Rijeka–AC Sparta Praha, canónico 2025-10-24 vs fecha jugada 2025-10-23); los otros 3 no tuvieron fixture canónico en esa ventana. No resolvió NULLs. No se compró, inició trial ni contactó al vendedor. No hubo DDL/DML ni recenso total; el último censo observado sigue en 4.605/24.593 finales FT con algún NULL (26.426 celdas), al 2026-10-20 23:59:12 UTC. Evidencia resumida y SHA-256 en la entrega privada `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/`.

## Muestras y leads API adicionales — 2026-10-21

Sports Data Vault publica una muestra gratuita de siete días, con licencia de investigación para un solo usuario y prohibición de redistribuir o re-alojar archivos. La muestra 2026-10-12–18 se evaluó en memoria (SHA-256 `3bff4357a104663bb260455fbe74ffeedef85947ad04c3da5e3e59a8a53057eb`): 2.721 partidos y 1.828 filas de estadísticas equipo-partido. Sus 32 partidos identificados como clasificación de FA Cup tenían `has_stats=0`; no había encuentros de las otras copas/torneos europeos objetivo. No aportó candidatos que cruzar con Neon; la descarga completa es de pago y está excluida. No se guardó archivo ni se adquirió producto. [Catálogo](https://sportsdatavault.com/en/data/) · [términos](https://sportsdatavault.com/en/terms).

TheStatsAPI publicó una ficha de FA Cup con Manchester City–Arsenal 2–1 el 14-sep-2026 e ID `mt_838955396`, que también aparece en el ejemplo EFL Cup. El calendario oficial de FA sitúa la cuarta ronda clasificatoria el 17-oct-2026, la primera ronda propiamente dicha el 7-nov y la entrada de clubes Premier en la tercera ronda el 9-ene-2027; la muestra no se valida como fixture real. Los términos limitan el almacenamiento y la licencia upstream no quedó acreditada. **Excluida del criterio gratuito vigente**; no se abrió cuenta, trial, clave ni se hizo llamada/contacto. [Ficha FA Cup](https://www.thestatsapi.com/football/league/fa-cup) · [términos](https://www.thestatsapi.com/terms) · [round dates oficiales de FA](https://www.thefa.com/competitions/thefacup/round-dates).

API-Football y Sportmonks quedan **excluidos del trabajo vigente**: las páginas públicas no acreditan la cobertura gratuita por fixture/temporada necesaria; las rutas exactas requieren autenticación. No se crearon cuentas o claves ni se hicieron consultas. Referencias históricas: [cobertura API-Football](https://www.api-football.com/coverage) · [cobertura Sportmonks](https://www.sportmonks.com/football-api/coverage/).

No se ejecutó una consulta nueva a Neon: se conserva como último censo observado el de 2026-10-20 23:59:12 UTC (**4.605/24.593** finales FT con algún NULL; 26.426 celdas). En este bloque no hubo DDL/DML ni valores nuevos. Evidencia externa, sin raws y con archivos `0600` en directorio `0700`: `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/CATALOG_AUDIT_SUPPLEMENT_20261021.json`; manifiesto SHA-256 verificado. Acta de entrega por fecha en `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/ACTA.md`.

## Auditoría complementaria de fuentes gratuitas — 2026-10-21 01:59:43 UTC

Censo `REPEATABLE READ / READ ONLY`: 24.593 finales FT; **4.603** con al menos un NULL en corners, tiros o tiros a puerta (**26.414 celdas**). No cambió Neon.

FPL Core Insights (`olbauday/FPL-Core-Insights`) publica 85 CSV por torneo para UEFA/EFL Cup de 2025/26–2026/27. Su README invita a reutilizar con atribución, pero GitHub no declara licencia SPDX y los registros incluyen FotMob IDs/URLs sin autorización upstream demostrada. El crosswalk READ ONLY usó 116 filas `finished`/`stats_processed`, 35 pares exactos de alias con alguna aparición histórica, y encontró **0** eventos dentro de ±1 día y **0** partidos canónicos únicos con FT coincidente. No aporta valores para los nulos actuales y no se descargó directamente información de FotMob.

Harvard Dataverse: el depósito `doi:10.7910/DVN/VCXQHY` declara CC0-1.0 y cubre nueve ligas en 2012/13–2024/25, pero la cabecera del archivo revisada por rango contiene resultados y covariables de plantilla, no corners/tiros/SOT. El depósito `doi:10.7910/DVN/G5SJXK` sobre UCL/UEL no lista archivos públicos. Mendeley Data mantuvo el texto de consulta pero mostró el listado genérico y errores React de hidratación; su API había requerido autenticación. Zenodo y GitHub repo-search devolvieron HTTP 403; se detuvo sin reintentos ni bypass. No se encontraron valores aplicables.

Evidencia y script privado, ambos modo `0600`, en `/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/`: `CATALOGS_FPL_HARVARD_MENDELEY_GITHUB_20261021.json` y `fpl_core_insights_crosswalk_readonly_v2.py`. No DDL/DML, cuentas, claves, trials, pagos ni valores nuevos. Manifiesto SHA-256 verificado en la carpeta de entrega.

## Búsqueda adicional en catálogos de investigación — 2026-10-21 02:12 UTC

Se archivaron nueve respuestas públicas (HTTP 200) de Hugging Face, DataCite, OpenAIRE, Figshare y la página oficial de football-data.org, con URL, fecha, tamaño y SHA-256, en `PUBLIC_CATALOGS_TARGETED_20261021.json` (SHA-256 `27b5cf336258567b930eaa2acbc53bef328dd9e9009f3648edba8620b4db5334`). Tres búsquedas guardadas de Hugging Face devolvieron listas vacías. OpenAIRE no encontró datasets titulados FA Cup; los cuatro registros de la consulta `UEFA football` son referencias institucionales/académicas y no dataset de estadísticas de partido. Figshare describe el corpus público de eventos recopilado por Wyscout para cinco ligas (La Liga, Serie A, Bundesliga, Premier League, Ligue 1), FIFA World Cup 2018 y UEFA Euro 2016; no enumera copas nacionales ni competiciones europeas de clubes y no se descargaron archivos.

DataCite arrojó un dataset Big-5 2022/23 con licencia CC BY-NC-ND y caveat de upstream en otro dataset EPL; el depósito IEEE CC BY 4.0 describe seis ligas (Liga MX y cinco europeas) sin copas. Otro resultado se limita a partidos de Copa Mundial; ninguno cubre las competiciones/temporadas residuales identificadas. La página oficial football-data.org declara que el plan gratis incluye fixtures/resultados pero no estadísticas; corners y tiros aparecen en un add-on de €15/mes, incompatible con el mandato de usar solo fuentes gratuitas. La página de API-Football devolvió challenge 403; no se repitió ni se intentó sortearlo. El buscador integrado permanece sin credencial configurada y no se alteró esa configuración.

No hubo descarga de archivos de datasets, cuentas, API keys, pruebas convertibles, pagos, DDL/DML ni nuevos valores. El censo que sigue vigente es el READ ONLY de 01:59:43 UTC: 4.603/24.593 finales FT con algún NULL (26.414 celdas); esta búsqueda no lo recalculó. CI del SHA `83f8a0b` está verde 4/4. Se conserva evidencia externa bajo permisos privados.

## Revisión de repositorios públicos con estadísticas — 2026-10-21 02:24 UTC

CI del commit documental `90b5973` terminó 4/4 verde (run `39531836396`). GitHub code search mostró `xgabora/Club-Football-Match-Data`, 238.858 partidos en 38 códigos de liga/división con `HomeShots`, `HomeTarget` y `HomeCorners` por lado. El README atribuye los datos a Football-Data.co.uk y describe ligas/divisiones; no declara permiso separado del upstream ni copas/UEFA objetivo. El repo marca MIT, pero eso no basta para acreditar los derechos del upstream. No se descargó el archivo `Matches.csv` (45.370.018 bytes) ni se utilizó.

Otro resultado UCL (`iAboud98/champions-league-winner-prediction-2025-2026`) lista columnas de estadísticas en README, pero no publica el CSV anunciado y no declara licencia. `withqwerty/football-docs` es una guía de proveedores, no un dataset, y no declara licencia; su lista remite a FBref por scraping y a Football-Data.co.uk para ligas, sin cubrir copas objetivo.

La búsqueda integrada de OpenClaw no funciona sin `GEMINI_API_KEY` y no se alteró configuración. Google mostró una página `/sorry`; la lectura de texto de Brave agotó timeout en dos intentos y se detuvo. GitHub code search fue la única ruta adicional accesible. No hubo descargas, cuentas, claves, pagos, contacto a terceros, DDL/DML ni valores nuevos. El censo de referencia se mantiene en el READ ONLY de 01:59:43 UTC: 4.603/24.593 finales FT con NULL (26.414 celdas); no se recalculó en esta revisión. Evidencia privada, con manifiesto SHA-256, en `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/GITHUB_FREE_STATS_REPOSITORY_REVIEW_20261021T0224Z.json`.
