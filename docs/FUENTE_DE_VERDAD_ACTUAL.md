# FUENTE_DE_VERDAD_ACTUAL — AnalyticsPredict

Este archivo es el punto de entrada oficial para trabajo operativo y técnico.

> **Estado operativo 2026-10-05:** AnalyticsPredict funciona localmente como herramienta personal single-user, sin login, pagos, suscripciones ni tiers. Neon fue migrada tras backup verificado: 182 apuestas NBA, 13 de fútbol, 7 combinadas y 16 selecciones conservadas. La configuración proviene de la cuenta con mayor actividad; por instrucción posterior del propietario, **todos** los registros deportivos son historial personal visible. La procedencia original permanece en el backup privado. `docs/reactivacion_single_user/` gobierna el trabajo nuevo. C0–C7 y la estrategia comercial descritos debajo son históricos, no tareas vigentes.

## Qué es AnalyticsPredict hoy
Plataforma analítica de decisiones deportivas con foco operativo (calidad de datos, contratos API, métricas, política de operación y trazabilidad), no una app de picks masivos.

## Qué documento manda
1. `docs/FUENTE_DE_VERDAD_ACTUAL.md` (este archivo)
2. `docs/arquitectura/ESTADO_PROYECTO.md` (estado formal por bloques)
3. `docs/reactivacion_single_user/ROADMAP_REACTIVACION_ANALYTICSPREDICT.md` (plan vigente)
4. `docs/reactivacion_single_user/DEUDA_TECNICA_PRIORIZADA.md` (prioridades técnicas)
5. `docs/borlty-context/` (contexto histórico complementario)

## Prioridades activas

- **Datos multi-fuente de fútbol, 20/10–21/10:** [censo, cruces y límites](reactivacion_single_user/RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20.md). Última transacción `REPEATABLE READ / READ ONLY` **2026-10-21 01:59:43 UTC**: 24.593 finales FT, **4.603 partidos con NULL (26.414 celdas)**; por código interno: ENG_FACUP 862, ESP_COPA 338, EUR_CHAMPIONS 336, EUR_CONFERENCE 968, EUR_EUROPA 796, FRA_COUPE 1.104 e ITA_COPPA 199. Persisten 236 vínculos, **1.386 valores NULL-only** y 1.398 observaciones. Separación de los gaps: **97 ESPN_SOCCER** y **4.506 SOFASCORE**. Los 97 ESPN están auditados 97/97 y los summaries tienen `statistics=[]`; no hay valores objetivo en esa cohorte. El dataset gratuito local Kaggle FA Cup/Coppa Italia tiene 8.856 filas, pero cruzó **0** canónicos por identidad única (equipos/aliases exactos y fecha ±1 día). El último lote aplicado fue Kaggle: 2 partidos Coupe de France/12 stats, score corroborado por ESPN, FT canónicos preservados. Regla: solo fuentes gratuitas con derechos/upstream claros; nada de pagos, trials, scraping contra términos o bypass. No hay fuente gratuita integral validada. Fuentes oficiales confirmaron ejemplos fuera de sus códigos (Fredrikstad–Molde, Copa Noruega, bajo ENG_FACUP; Sporting–Nacional, Allianz Cup/Taça da Liga, bajo ITA_COPPA). `pais_id` faltante impide estimar extensión; no imputar país ni recategorizar. Evidencia `SOURCE_SPLIT_AND_FREE_CROSSWALK_20261021T014525Z.json`, `GITHUB_HTML_FREE_SOURCE_SEARCH_20261021T0148Z.json` y acta privada bajo `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/`.

Revisión histórica de fuentes: Sportmonks, StatPal/SoccerDataAPI, Goalserve, Stats API y Footballdata.io no demostraron acceso gratuito abierto con cobertura/retención compatible para los gaps; quedan excluidas, no son opciones vigentes. Se excluye también `vsntll/xValue` por licencia de datos ausente y restricciones de FotMob. No se crearon cuentas, claves o pruebas. Evidencia histórica en `SPORTMONKS_SOURCE_AUDIT_2026-10-20/`; no hubo valores nuevos.

Ampliación de catálogo 20/10: `xgabora/Club-Football-Match-Data` anuncia 38 códigos de liga/división y licencia MIT del repositorio, pero atribuye sus estadísticas al upstream Football-Data.co.uk; no se confirmó una licencia separada de los datos ni cobertura de copas UEFA/nacionales. Los resultados revisados en Hugging Face/Zenodo eran ligas top-5, resultados/minutos de gol, un dataset UEFA no comercial y estrecho, o carecían de procedencia/licencia suficiente. No se descargaron esos CSV. Se evaluó in-memory una muestra HF de 20 partidos UEFA: 5 tenían stats, pero solo 2 coincidieron con partidos canónicos y ambos ya estaban completos; 3 no tuvieron match canónico en ±1 día. El producto completo del vendedor es de pago, bajo licencia `single-commercial-user`, cubre UCL/UEL/Conference pero no copas nacionales; el README dice que la mayoría de las clasificatorias UEFA no se incluyen. El campo `Goal_Attempts` no tiene equivalencia documentada a tiros totales. Queda excluido por la instrucción posterior del propietario de usar únicamente fuentes gratuitas; no hubo compra, trial ni valores aplicados. El último censo observado continúa siendo el READ ONLY de 23:59 UTC (4.605 partidos/26.426 celdas con NULL); la consulta puntual `READ ONLY` no modificó Neon ni recalculó el censo. Evidencia privada `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/`.

Continuidad 21/10: el sample gratuito de Sports Data Vault no contiene estadísticas en sus 32 partidos de clasificación de FA Cup y no presenta encuentros de las otras copas/torneos europeos residuales; no se importó. TheStatsAPI queda fuera hasta validar sus fixtures de muestra y compatibilidad de retención con la base/modelos. API-Football y Sportmonks mantienen cobertura promocional pero requieren autenticación para comprobar temporadas/fixtures; no se crearon cuentas, trials ni claves. Sin nueva consulta/escritura a Neon; el último censo observado sigue en 4.605/24.593 partidos y 26.426 celdas NULL. Evidencia: `FUTBOL_DATASET_CATALOG_AUDIT_2026-10-20/CATALOG_AUDIT_SUPPLEMENT_20261021.json`; acta de entrega `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/ACTA.md`.

**Restricción operativa aclarada por el propietario (21/10): solo fuentes gratis, sin prueba que pueda convertirse en cobro.** Las referencias de precios anteriores quedan como descartes históricos; no se contratará ni pagará proveedor. Se comprobaron las páginas CSV de FootyStats para copas/UEFA: publican conteos por temporada, pero el único sample anunciado sin registro es EPL 2018/19, ampliar descargas consume créditos y los términos prohíben acceso/extracción automatizados salvo autorización por API; no se usará para completar esta BD. StrikerAPI anuncia 500 créditos gratis mensuales sin tarjeta y permite almacenamiento/modelado bajo sus términos, pero exige cuenta y email verificado, declara que sus datos derivan de ESPN, no enumera las copas nacionales objetivo y advierte que las clasificatorias UEFA suelen estar sin boxscore. No valida los gaps restantes ni una solución integral; no se creó cuenta ni se hizo llamada. Datasets libres nuevos revisados fueron solo resultados/fixtures, duplicados de la fuente HF ya auditada, de una fase UEFA que no presenta gaps, o sin licencia/procedencia suficiente. Sin clave, pago, trial, descarga nueva, cuenta, cambio en Neon ni valores nuevos; el censo observado sigue siendo 4.605/24.593 partidos con NULL (26.426 celdas) del 20/10 23:59 UTC. Evidencia resumida: entrega privada `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

Ampliación READ ONLY del 21/10 01:59:43 UTC: FPL Core Insights publica 85 CSV por torneo para UEFA/EFL Cup 2025/26–2026/27 y su README invita a reutilizar con atribución, pero no declara licencia SPDX; los registros usan IDs/URLs de FotMob y no se acreditó permiso upstream. El cruce estricto de sus 116 filas finalizadas/estadísticas procesadas dio 35 pares exactos de alias en alguna fecha, 0 dentro de ±1 día y 0 partidos canónicos únicos con FT coincidente; no aporta NULLs existentes y no se importó. Harvard Dataverse ofrece un archivo CC0 con resultados/composición de planteles, sin corners/tiros/SOT; su otro depósito UCL/UEL no lista archivos públicos. Mendeley falló hidratación de la interfaz y mostró resultados genéricos; Zenodo y GitHub repo-search devolvieron 403 y no se reintentaron. Sin cambios de Neon. Evidencia: `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/CATALOGS_FPL_HARVARD_MENDELEY_GITHUB_20261021.json`.

La búsqueda pública ampliada encontró un candidato con estadísticas de copas/UEFA en Kaggle (`ivanposinovec/football-matches-from-europe-and-south-america`) y otro con clasificatorias UCL 2020–2026. Ambos quedan excluidos: el primero declara scraping de FBref y aceptación de términos de Sports Reference pese a la etiqueta CC0 del espejo; el segundo tiene licencia “Other” y no aclara fuente/upstream ni permiso persistente. El dataset Wyscout CC BY 4.0 está limitado a top-five leagues 2017/18 y torneos de selecciones, no a los gaps objetivo; su descarga de 3,23 GB no se justificó. No se descargaron estos candidatos. El resto son estadísticas de otra copa/temporada, métricas parciales, resultados sin stats o agregados. Ninguna fuente gratuita con derechos claros ha cubierto todo el residual; no se cambió Neon. Evidencia `FUENTES_MULTIFUENTE_FUTBOL_2026-10-21/FREE_SOURCES_REVIEW_20261021.json`.

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
