# Base local multiliga y paquete Windows actualizado — 2026-10-30

## Uso personal

- [x] Base local permite NBA, Euroliga y WNBA sin base de datos. Cambiar liga limpia equipos y resultado anterior; cancela consultas y descarta respuestas tardías.
- [x] NBA conserva su contrato `consulta-local-v1`, sus 48 minutos y su restricción sobre push no acreditado. No se han cambiado pesos ni probabilidades del modelo.
- [x] Euroliga usa su publicación original de 40 minutos y su normal discretizada con push; no usa modelos NBA ni parciales en esta consulta.
- [x] WNBA reutiliza exclusivamente `ajuste_final` REG ya publicado, de 40 minutos. No pasa por `analizar`, `ajuste_cache` ni `ajustar_alcance`: no hay ajuste implícito por temporadas ni journal.
- [x] Cada catálogo conserva identidad de liga y soporte del ajuste. Equipos sin muestra suficiente no se habilitan en el formulario; el motor también exige sus mínimos.
- [x] Las consultas nuevas usan `consulta-local-v2` y se guardan/reabren con liga, versión, corte, parámetros y probabilidades originales. Siguen abriendo las copias NBA v1.
- [x] El comparador de líneas discretas muestra over/under/push por aproximación matemática de la misma distribución, sin nuevo POST ni afirmación de calibración. NBA conserva el comparador continuo para `.5`.
- [x] Estado del sistema muestra el modo real de ejecución, los artefactos utilizables y qué funciones requieren BD. En modo base omite la consulta de inventario SQL.
- [x] Diagnóstico JSON descargable: timestamp, disponibilidad e identidad de modelos; sin configuración SQL, credenciales, rutas privadas ni notas del cuaderno. Una actualización fallida conserva y rotula la última lectura.
- [x] Las fechas con hora del estado se muestran en America/Bogota. Las fechas sin hora no se convierten de zona.
- [x] Tema claro: los avisos y estados legacy de tonos pálidos usan los colores semánticos del tema; los campos deshabilitados conservan un fondo coherente. El tema oscuro mantiene sus tonos.

## Identidad estadística

- [x] No se entrenó, publicó ni activó ningún modelo nuevo. No se presentan mejoras de MAE, calibración o eficacia.
- [x] En WNBA el hash y la muestra del ajuste REG son distintos del dataset REG/POST embebido: se devuelven ambos hashes y la versión del ajuste; el corte mostrado corresponde al ajuste realmente usado.
- [x] La publicación WNBA existente contiene 1.997 registros embebidos; su ajuste REG contiene 1.840 finales hasta 2026-09-24. Esos números no son una nueva lectura de BD ni un test independiente.
- [x] Se mantienen las abstenciones originales. No se activó el fallback experimental ni se transfirieron covarianzas entre ligas.
- [x] Una distribución calculada con el artefacto no verifica fixture, plantillas, lesiones, forma reciente ni cobertura deportiva actual.

## Preparación Windows

- [x] `scripts/preparar_instalacion_local.py` prepara una carpeta nueva con el código integrado del working tree, frontend compilado, estado íntegro original y herramientas de migración verificadas.
- [x] Incluye cambios locales y archivos nuevos del proyecto. Conserva HEAD e índice; no usa un checkout antiguo como si incluyera las mejoras actuales.
- [x] Excluye `.git`, dependencias, entornos reales, logs/dumps y archivos de credenciales conocidos. Es una copia privada local, no una publicación ni una certificación universal de ausencia de secretos en todo el repositorio.
- [x] SHA-256 por archivo e identidad agregada del producto; comprobación de cambios de fuentes/inventario durante la copia. Rechaza destinos existentes, enlaces y rutas que salgan de las fuentes.
- [x] La copia depende del Python Windows ya instalado; no es un instalador autónomo ni duplica `.venv` o `node_modules`.
- [x] El paquete incluye `ABRIR_BASE_LOCAL.cmd`, configuración de rutas sin contraseñas y `CONTINUAR_MIGRACION.ps1`. El script usa el código del paquete nuevo y no la aplicación anterior.
- [x] `CONTINUAR_MIGRACION.ps1 -SoloPreflight` verifica preparación sin conectar ni restaurar. La ejecución completa sigue exigiendo exportación vigente consistente del origen y un destino nuevo exclusivo.
- [x] El comprobador del lanzador verifica `/api/local/estado` además de salud; exige al menos un artefacto utilizable. `--estado` puede contener únicamente WNBA o Euroliga; no obliga a tener NBA.
- [ ] Migración Windows completa: pendiente de exportación vigente. La cuota del origen volvió a impedir la lectura el 30 de octubre. No se ejecutó el camino de restauración real.

## Continuidad de los pendientes científicos

- [ ] L06/L07/L08 NBA: falta snapshot elegible completo y, para dispersión, residuos fuera de muestra. El artefacto no sustituye el dataset de entrenamiento.
- [ ] L09: falta evidencia independiente del refit/cohorte futura; EVAL de desarrollo ya fue observado. No puede renombrarse como test intacto.
- [ ] L10 V4: faltan desarrollo y cohorte corregidos originales con sus identidades; una regeneración no los sustituye.
- [ ] L11 y parte Euro de L12: falta TRAIN/CAL/EVAL completo; coeficientes y muestras del artefacto no permiten reconstruir esos targets.
- [ ] Parte WNBA de L12: el ensayo existente eligió k0 y no acreditó ganancia adicional; se conservan gates y modelo publicado.
- [ ] L13/L14: falta BD legible para conteos causales y medición de cobertura prioritaria. Favoritos y páginas recorridas no acreditan calendario completo.
- [ ] L29: falta fuente temporal de reloj/posesiones y evaluación; parciales al cierre de cuarto no equivalen a live.
- [ ] L30: faltan fuentes con identidad y disponibilidad temporal acreditadas de lesiones/alineaciones/xG. No se introducen defaults ficticios.

## Verificación

- [x] Suite completa frontend: 218 aprobadas, 0 fallidas y 0 omitidas. Tras estabilizar el callback del estado se repitieron sus 5 pruebas, todas aprobadas. Lint final sin errores ni avisos; TypeScript y build aprobados tras el último cambio de código.
- [x] Selección backend pertinente: 133 aprobadas y 2 omitidas de integración dependiente de BD; no equivale a ejecutar toda la suite contra una BD deportiva restaurada.
- [x] Navegador real con los artefactos existentes: WNBA total y Euroliga Q1 exportados, parámetros/probabilidades idénticos a sus motores originales. WNBA guardada y reabierta sin otro POST; un POST por liga en todo el recorrido.
- [x] Estado sin BD y diagnóstico descargado desde la UI; cero llamadas al inventario SQL del estado en ese recorrido. Consola sin errores observados.
- [x] Tema claro verificado a 1272 px: aviso RGB(118,80,0) sobre fondo RGB(243,245,247), sin desbordamiento horizontal. Se restituyó el tema oscuro de la prueba; móvil no acreditado.
- [x] Los 38 archivos originales de estado y sus copias de prueba conservaron sus hashes. HEAD e índice conservados.
- [x] Pruebas de igualdad con los motores congelados, abstenciones y rutas sin BD/fit/journal; separación de hashes y ligas.
- [x] Pruebas de guardado/reapertura v2 con push, cancelación entre ligas, reintento de catálogo y diagnóstico sin SQL.
- [x] Pruebas del preparador con repositorio temporal: código modificado/no versionado, exclusiones, integridad, destino existente, traversal y fuentes que cambian durante la copia.
- [x] Los resultados exactos y la ruta de la última copia preparada se recogen en el informe acumulado externo y sus recibos. Este documento no atribuye una prueba sintética a datos deportivos reales.

## Archivos principales

- [x] Backend: `api/rutas_local.py`, `servicios/consulta_local_ligas.py`.
- [x] Frontend: `PaginaBaseLocal.tsx`, `PaginaCuaderno.tsx`, `PaginaOperacion.tsx`, `consultaLocal.ts`, `estadoLocal.ts`.
- [x] Windows: `iniciar_local.py`, `preparar_instalacion_local.py`, `servir_frontend_local.py`, `plantillas/continuar_migracion_actualizada.ps1`.
