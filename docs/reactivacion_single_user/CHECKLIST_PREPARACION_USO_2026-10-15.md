# Checklist de preparación para uso — 2026-10-15

**Orden del propietario:** implementar el diagnóstico y actualizar completados y
pendientes con evidencia. Base `ebf128c`, rama `reactivacion/implementacion-single-user`.
`[x]` significa resultado comprobado, no certificación predictiva. `[ ]` conserva
el motivo de bloqueo/en curso. Evidencias sin secretos fuera del repo:
`Carpeta de Entregas de Borlty/PREPARACION_USO_INTEGRAL_2026-10-15`.

## A. Entorno y flujo local

- [x] Crear `backend/.venv` persistente con Python 3.12 y `requirements.lock`.
- [x] Verificar dependencias frontend y compatibilidad de Node local/CI. Node24 local: lint, 19 tests y build verdes; CI usa Node20.
- [x] Arranque reproducible en loopback, sin parar procesos ajenos ni autoentrenar. `scripts/dev.sh`, 8000/5173 HTTP200; salud con30 equipos.
- [x] Smoke HTTP de Dashboard, NBA, fútbol, bitácora y Estado: seis GET API y seis rutas frontend HTTP200; calendario canónico devuelve49 próximos. Rutas activas sin login en código/OpenAPI.
- [ ] Smoke visual en navegador. Herramienta rechazó navegación local; diagnóstico técnico del agente con control autorizado, no revisión delegada al propietario. HTTP y componentes no lo sustituyen.

## B. NBA: dominio, calidad y actualización

- [x] Filtrar NBA explícitamente y excluir invalidados/0–0/cuarto inválido en entrenamiento, backtest y consultas dependientes. Selector/conteos/temporadas comunes; lookups de registro delimitados a NBA.
- [x] Probar con PostgreSQL sintético mezcla NBA/Euroliga, inválidos y cutoffs. Regresión real del selector y rollback completo del ingestor.
- [x] Rechazar en serving artefactos sin dominio/calidad acreditados; no seguir sirviendo el mixto de 58 entidades como NBA. Formato2 con dominio/política explícitos.
- [x] Actualizar NBA con dry-run, backup, ingesta controlada y postflight/idempotencia. 73 filas nuevas (33 playoffs+40 PRE), una exhibición fuera de dominio excluida por ID; cero filas históricas sobrescritas.
- [x] Entrenamiento explícito NBA con 30 equipos, dataset/versiones identificados y backup del artefacto previo; recarga sin nueva escritura. Modelo2123 publicado con30 equipos y último dato de entrenamiento2026-06-14; servicio recargó2123 sin crear otra versión.

## C. Fútbol canónico

- [x] Acreditar correspondencias ESPN↔competición/temporada/clubes, incluidos ascendidos; no usar similitud automática. Manifiesto externo de96 clubes revisados contra catálogo/variantes/alias y rosters2026; dos altas (Hull/Coventry), cinco temporadas2026–27 con evidencia de scoreboard.
- [x] Implementar vínculo/ingesta canónica con procedencia, NULL, anti-duplicados y preservación del histórico; rollback DDL+DML sobre contrato/datos reales y CI2378058 4/4.
- [x] Aplicar con backup/postflight y conectar calendario/estadísticas al flujo API/UI. Neon337 eventos/200finales/136programados/1suspendido; dos clubes/cinco temporadas nuevas;23.919 históricos y seis huellas de apuestas/predicciones intactas, reimportación0/0;49 próximos en API del frontend.
- [x] Verificar modelos/calibradores de fútbol antes de actualizar. No hay versión activa registrada; predictor sin archivos inicializa modelos vacíos, gestor legacy espera columna inexistente. Los nuevos FT carecen de1T/2T: no se entrenó ni activó calibrador/modelo.
- [x] Reparar persistencia/serving ML fútbol y verificar dataset por target antes de reentrenar. Artefacto completo en JSONB, activación/recarga verificadas en PG sintético, sin entrenamiento en serving;771backend/24frontend/lint/build. Diagnóstico real: corners14.136/goles10.716 hasta marzo, disparos14.379 hasta12/10. Sin DDL/DML ni versiones nuevas fútbol en Neon. Ver `PERSISTENCIA_ML_FUTBOL_2026-10-15.md`.
- [x] Evaluación retrospectiva por familia y ventana con particiones por partido, baseline e intervalos ejecutada.581EVAL corners/goles y618disparos;784backend en el WIP. Ninguna familia pasa todos los gates; no se guardó/activó fútbol enNeon. Ver `EVALUACION_TEMPORAL_FUTBOL_2026-10-16.md`.
- [x] Completar200finales con goles/córners1T/2T acreditados, sin repartirFT. Backup/rollback/CI/idempotencia/postflight; flag de córners derivado por trigger verificado. Ver `SIETE_FRENTES_2026-10-16.md`.
- [ ] Activación fútbol solo tras aptitud. Reevaluación618EVAL/familia:79,13%cobertura en las tres y targetcorners peor; ninguna apta. CensoCAL97<100mínimo, no se aflojan gates.

## D. Operación y evidencia

- [x] Rutina manual explícita/idempotente y estado read-only de fuentes, frescura, modelos y jobs, sin notificaciones externas. API/UI Estado más runbook `OPERACION_Y_PROSPECTIVA_2026-10-15.md`; ausencia/fallo no convertidos en cero.
- [x] Cadena prospectiva instalada tras ensayo/rollback/CI2b142e0 4/4. Evento/mercado/hora UTC/features/coeficientes/dataset/modelo/raw/calibrador ausente explícito; reloj BD y registros inmutables. Nueve huellas históricas intactas. Resolución ESPN idempotente probada, no acredita independencia ni outcome real aún.
- [x] E2E aislada y captura real anterior al inicio.12eventos NBA del scoreboard2026-10-16, todos de PRE, umbral técnicoQ1=55.5 predeclarado; congelados desde2026-10-16T02:09Z para inicios23:00Z–02:30Zdel17. Reimportación0,12hashes/horas/políticas verificados por lectura independiente.0outcomes reales; sin picks/stakes/recomendaciones, sin retrofechar ni mezclar con NBA descriptivo.
- [x] Unificar gates de publicación SQL/API/UI de consumidores activos: P&L cross-sport sin soportes/N/D, grano/cohortes, calibración con muestras y sinTTL; auditar78GET, protegerGET/HEAD y sanitizar fallos. Ver `KPI_PNL_Y_GET_2026-10-16.md`. No reescribir apuestas dudosas. Subbloque ML fútbol cerrado: modelos y fechas ficticios retirados, N/D preservado y métricas in-sample explícitas; calibraciónAPI/UI16/10 separa series/n/modelo, N/D y frescura sinTTL (794backend/27frontend,4GETreales200/7huellasintactas). El cierre técnico residual se acredita16/10 en KPI_PNL_Y_GET; no cierra M12 científico.
- [x] Evaluación científica descriptiva por modelo/mercado/origen/serie, n e IC y confidence/odds realizada;1.303cohortes n2–4, cero elegibilidad temporal/calibradasID. No calibrador ni certificación fabricados.
- [ ] Acumular outcomes futuros y validar walk-forward/calibración/confidence con n e intervalos. **Pendiente temporal: requiere que ocurran partidos después del congelamiento.**
- [x] Registrar la decisión definitiva del propietario: NO existen soportes originales de stake/cuota/ganancia. No hay recuperación documental pendiente suya. Conservar exclusiones/ROI N/D y filas; no certifica las67binarias solo aritméticas. Propagación integral se verifica en el bloqueKPI.
- [ ] Verificar fuente permitida independiente para resultados/inicio. **Bloqueado:** ambos schedule públicos NBA CDN devolvieron403; sin evasión. Dos consultas ESPN no son independencia. CBS12/12calendarios y cuartos/FT de un finalprobe acreditan publicación distinta, no upstream independiente.

## E. Publicación y cierre

- [x] Código2b142e0 publicado, diff/secretos revisados, CI38838845268 4/4,751backend/21frontend/lint/build. Estado/changelog/checklist actualizados; cierre documental se verifica por separado.
- [x] Cierre HTTP y pruebas UI con informe/checklist/memoria actualizados; visual manual conserva su casilla bloqueada. Entrega `PREPARACION_USO_INTEGRAL_2026-10-15`; HEAD/CI documental y limpieza final se registran en su acta antes del cierre visible.

H4 integral y H12 restantes conservan su plan previo; no iniciar purga parcial de
historia ni cambios globales. El bloque D de evolución avanzada sigue fuera de alcance.

## Registro

- 2026-10-15: checklist creado y entorno backend persistente instalado con lock.
  No se inició entrenamiento ni se alteró Neon para probar el entorno.
- 2026-10-15: CI337288d 4/4; detectado contrato hashvarchar32 al entrenar, corregido en852f4ba con CI38837332780 4/4, sin repetir73 filas deportivas ni publicar artefacto fallido. Modelo2123 ya activo,30 equipos. Datos ajenos/apuestas/predicciones intactos. Browser visual bloqueado por política de navegación local; HTTP comprobado, sin sortear la política.
- 2026-10-15: fútbol2378058 CI38837743890 4/4 y aplicación verificada. Primer intento revirtió por lock sin residuos; segundo completo. Operación/prospectiva:751 backend,0fallos/omitidas,21frontend/lint/build. Captura real y CI de este último lote aún pendientes al registrar esta entrada.
- 2026-10-15, posterior:2b142e0 CI38838845268 4/4; cadena instalada y12capturas reales prospectivas en Neon, sin afectar nueve huellas históricas. APIEstado200 y12/0. La entrada previa de pendientes es histórica; siguen abiertos outcomes futuros, independencia, KPI residual, ML fútbol, visual y procedencia P&L.


## Pasada integral posterior16oct — prevalece sobre conteos anteriores

- [x] Recuperar426finales adicionales con evidencia de goles1T/2T yFT/tiros; backup,
  rollback/idempotencia/postflight,38colisiones retenidas sin duplicar. No incorporar
  nuevos córners por mitades de cronología no conciliable.
- [x] Incorporar163programados noviembre conNULL y controles; total24.845fútbol.
- [x] V2estacional + CLI preparación/evaluación y pruebas;199fixturesfuturos,
  163predicciones/36abstenciones por familia. Techo81,91%<90%, no activable.
- [x] DiagnosticarV3reserva100 antes de outcomes sin bajar mínimos:CAL88/78<100,
  sin candidato. Conservar versiones y fallos, no elegir por futuro observado.
- [x] Añadir2finalesNBA PRE y capturar3REG20oct con ensayo/backup/huellas;
  12PREoriginales intactos,15hashes/horas verificados,0outcomes.
- [x] H12migración aislada completa:0alertas/npm10ci/29tests/lint/build, sin publicar.
- [x] Preparar solicitudGitHub y propuesta mínima de navegación global, sin aplicar
  políticas ni enviar a terceros. Decisiones del propietario solo al cierre.
- [ ] ActivarMLfútbol/certificar eficacia: sigue sin aptitud/muestra elegible.
- [ ] Visual/publicarH12/purgaGitintegral: dependencias de alcance/proveedor.

Detalle: [validación estacional y fases NBA](VALIDACION_ESTACIONAL_Y_FASES_NBA_2026-10-16.md).
