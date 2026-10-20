# Recuperación multi-fuente de estadísticas nulas — 2026-10-20

## Estado vigente

**Recuperación parcial aplicada; la búsqueda continúa y el catálogo de fútbol no está completo.** Los backfills tocaron únicamente seis métricas por partido finalizado: corners FT, disparos totales y tiros al arco, lado local/visitante. No modificaron goles, partidos futuros, apuestas, modelos ni predicciones.

Los `NULL` siguen significando dato desconocido/no publicado, nunca cero. Un valor canónico no nulo no se sobrescribe. Las fuentes con identidad ambigua, discrepancia o derechos/contrato insuficientes quedan excluidas. La cantidad de partidos con nulos no representa una cantidad recuperable.

## Censo actual de Neon — READ ONLY, 2026-10-20

- **24.593** partidos finalizados con FT.
- **4.605 partidos** aún tienen al menos un `NULL` en las seis métricas objetivo; suman **26.426 campos nulos**.
- Nulos por campo: corners local **4.094**, corners visitante **4.094**, disparos local **4.585**, disparos visitante **4.585**, tiros al arco local **4.534**, visitante **4.534**.
- Partidos con gaps por competición: ENG_FACUP 862; ENG_PREMIER 0; ESP_COPA 338; ESP_LALIGA 0; EUR_CHAMPIONS 336; EUR_CONFERENCE 968; EUR_EUROPA 796; FRA_COUPE 1.106; FRA_LIGUE1 0; GER_BUNDESLIGA 0; ITA_COPPA 199; ITA_SERIEA 0.
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
| StatsBomb Open Data | 1.819 partidos listados; 155 cruces candidatos exploratorios con fecha/equipos/FT. Ninguno de esos 155 tenía nulos en las diez métricas corners/tiros examinadas; el kickoff de algunos archivos carece de zona horaria acreditada. | No se encontró un gap objetivo utilizable ni se elevan candidatos ambiguos a vínculos de aplicación. |
| PitchAPI y football-data.org | PitchAPI documenta estadísticas, pero su endpoint requiere clave y no se verificó cobertura real; football-data.org anuncia corners/tiros como complemento pagado. | No se recibió clave ni se compró plan. |
| FBref, TheSportsDB, football-data.co.uk | Se observaron 403/desafío o timeout en las consultas previas. FFF/UEFA y otros sitios oficiales están sujetos a condiciones de reutilización distintas. | No se sortean bloqueos ni se automatizan sitios cuyos términos lo prohíben. No se atribuyen datos no publicados. |

Un barrido adicional de catálogos Kaggle/Hugging Face/GitHub encontró copias de Adamgbor con upstream Football-Data.co.uk; `WideMan/football_matches` sin licencia declarada y sin cobertura de copas objetivo acreditada; un dataset HF de detección de imágenes; mirrors FBref sin términos claros; y un conjunto reciente francés/alemán que solo contiene marcador, fecha y equipos. No aportan una fuente nueva utilizable. También se confirmó que el mirror HF de Sporoseseun es una copia binaria exacta del dataset HF ya auditado, sin cobertura independiente. No se usaron fuentes con métricas sin upstream/licencia claros. El extractor de búsqueda web configurado no tuvo clave; no se alteró Gateway ni se intentó eludir ese requisito.

## Código y operación

- `backend/servicios/resolucion_multifuente_futbol.py`: validación de eventos/identidad, extracción por campo y proveedor, hash, consistencia y merge que conserva valores no nulos. La regla general de hora no se relajó; la excepción +5 h está limitada al importador SofaScore y ESPN en el mismo día UTC.
- `backend/servicios/proveedor_pitchapi.py`: cliente documentado, GET y errores sanitizados; no se usó sin API key.
- `backend/migrations/2026-10-20_observaciones_multifuente_futbol.sql` y allowlists de `DATAHUB_FOOTBALL_DATA`, `KAGGLE_GOKHANERGUL` y `HF_EATPIZZANOT`: la tabla y constraints necesarios existen en Neon y la procedencia de las tandas aplicadas está registrada.
- Scripts de auditoría/aplicación por proveedor en `backend/scripts/`; modo de solo lectura por defecto cuando corresponde, DML explícito, guardas `IS NULL`, lock, backup externo, rollback y postflight.
- No se reentrenó ni activó modelo, no se modificaron apuestas/predicciones, no se creó cron, no se contrató proveedor y no se automatizaron fuentes futuras.

La revisión vigente compiló el resolutor y el script Verona–Roma con `py_compile`, y pasó `git diff --check`. La ejecución predeterminada del script produjo `READ_ONLY_PREFLIGHT_OK`, confirmó el target corner `0`, el FT canónico `3–0`, la identidad y las tres observaciones existentes, con `database_changes=false`; evidencia en `VERONA_ROMA_CORNERS_ZERO/RUN_20261020T231726198596Z/`. Un recenso READ ONLY independiente de Neon confirmó 24.593 finales, 4.605 con gaps (26.426 campos), 234 vínculos y 1.386 observaciones; detalle por competición/campo en `CENSO_READONLY_CIERRE_20261020T231929Z.json`. No se ejecutó la suite local en esta pasada y el resultado de pruebas del checkpoint anterior no se presenta como validación de este cambio.

## Continuidad

Se sigue buscando cobertura admisible para los gaps de copas nacionales y torneos UEFA. Los 4.605 partidos residuales quedan abiertos: no hay una fuente verificada para completar todo el catálogo ni ETA confiable. Mantener `NULL` cuando falte evidencia. No declarar “datos completos” hasta un censo nuevo y un postflight por campo/fuente.

Evidencia privada externa: `/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/RECUPERACION_MULTIFUENTE_SEGUIMIENTO_2026-10-20/`, en particular `CENSO_Y_FUENTES_ALTERNATIVAS_20261020T2257Z.json`, `CENSO_READONLY_CIERRE_20261020T231929Z.json`, `DATAHUB_LALIGA_RESIDUAL_CROSSWALK/application_result.json`, `VERONA_ROMA_CORNERS_ZERO/` (incluye aplicación y preflight READ ONLY posterior), `KAGGLE_CC0_TOP5_PROBE/`, `KAGGLE_GOKHANERGUL_FRANCE_GERMANY_NO_STATS_PROBE/`, `FUENTES_COPAS_BUSQUEDA_SUPLEMENTARIA_20261020.json`, `CATALOGOS_HF_KAGGLE_ADICIONALES_20261020.json` y `MANIFIESTO_SHA256.txt`. La evidencia permanece fuera del repositorio y no incluye secretos.
