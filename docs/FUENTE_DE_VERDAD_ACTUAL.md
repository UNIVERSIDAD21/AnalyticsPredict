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

- **Datos multi-fuente de fútbol, 20/10:** [censo, fuentes y límites](reactivacion_single_user/RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20.md). Recuperación parcial persistida: 234 vínculos proveedor-partido, 1.374 valores NULL-only y 1.386 observaciones de procedencia. Censo READ ONLY 23:59 UTC: 24.593 finales FT; 4.605 aún tienen algún NULL entre corners/tiros/SOT (26.426 campos), distribuidos en 53 grupos de competencia-temporada. Por competencia: ENG_FACUP 862; ESP_COPA 338; EUR_CHAMPIONS 336; EUR_CONFERENCE 968; EUR_EUROPA 796; FRA_COUPE 1.106; ITA_COPPA 199. Los gaps se concentran en copas nacionales y torneos UEFA; no todos necesariamente son recuperables. El cotejo UEFA 2025/26 muestra gaps solo en clasificatorias de julio/agosto (Champions 55, Europa 58, Conference 181); ESPN Scoreboard respondió HTTP 200/0 eventos en dos fechas de muestra y no hay vínculo ESPN para los 55 candidatos UCL. La fase principal observada sí muestra stats ESPN, pero ya tiene los seis campos completos; no es fuente independiente. StatsBomb cubre UCL solo hasta 2018/19 y Copa del Rey hasta 1983/84; sus cruces exactos previos no completan gaps y no cubre las otras copas residuales. Stats API declara estadísticas y un acuerdo comercial upstream, pero la cobertura requiere clave (probe público 401), no hay clave en Secret Store y su AUP prohíbe espejos masivos; no se descargaron ni aplicaron datos. Footballdata.io también documenta corners/tiros/SOT pero requiere key, no publica cobertura objetivo y sus términos pueden exigir permiso escrito para almacenamiento prolongado/replicación; no se creó cuenta ni se consultaron stats. El mirror GitHub jokecamp/FootballData mezcla upstreams y la licencia MIT del repo no acredita derechos de las estadísticas. También se descartaron dos repositorios sin licencia reconocida y con alcance temporal/competitivo ajeno a los gaps. TotalCorner se excluyó por sus términos contra extracción automatizada y FCStats por robots.txt/403. La excepción Verona–Roma completó un corner local explícito en tres fuentes y conservó el FT canónico 3–0. Footiqo permite export manual privado no comercial para UEFA, pero prohíbe automatizar descargas; el catálogo no lista copas nacionales y la cobertura UEFA por temporada sigue sin comprobarse (2.100 partidos/11.874 celdas potenciales en el censo). Su oferta premium anuncia 150.000+ partidos/60+ ligas y Advanced Stats Big Five+UCL+UEL, sin cobertura objetivo ni precio específico confirmados; no se solicitó muestra ni se compró. FootyStats requiere selección/contrato de copas. Sin nuevas escrituras, promesa de completitud, reentrenamiento, cambios de apuestas ni ingestas programadas.

Actualización de continuidad: Sportmonks documenta estadísticas por fixture (incluye corners/tiros), permite almacenar datos del API y prohíbe la reventa directa. Sus planes base exponen solo tres temporadas recientes por liga; la profundidad anterior depende de un add-on y disponibilidad variable. El free tier se anuncia públicamente, pero Coverage Finder requiere cuenta y no garantiza cada evento/campo; exactitud de las siete competiciones residuales no validada. StatPal/SoccerDataAPI y Goalserve también anuncian estadísticas/históricos, pero no se comprobó la cobertura por fixture/temporada y no se validaron términos para conservar los datos (StatPal no expuso términos accesibles; Goalserve deriva el trial a contacto). Se excluye `vsntll/xValue`: repo sin licencia que usa FotMob y sus términos prohíben acceso automatizado/sistemático; no se descargó ni usó. No se creó cuenta, no se obtuvo clave, ni se contactó o inició prueba. Búsquedas de metadatos en HF/GitHub no identificaron un dataset histórico/licenciado nuevo; el catálogo de Kaggle devolvió un challenge y no se intentó evadirlo. Evidencia: entrega privada `SPORTMONKS_SOURCE_AUDIT_2026-10-20/`. El censo permanece igual y no se aplicaron nuevos valores.

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
