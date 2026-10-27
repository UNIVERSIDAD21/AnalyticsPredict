# Agenda global de baloncesto · 26 de octubre de 2026

Entrada: `/baloncesto`. La agenda diaria abre Hoy sin filtrar por el motor elegido. Ofrece Mañana, fecha, días anterior/siguiente, búsqueda de equipos, filtros visibles de liga/estado y paginación. Quitar filtros incluye la búsqueda. El selector de liga del análisis manual es independiente del filtro de la agenda.

Seleccionar una tarjeta abre el motor NBA, WNBA o Euroliga y completa el partido/equipos. Cambiar de partido desmonta el controlador anterior y elimina su salida. La URL conserva fecha, liga y partidoId; atrás/adelante y recarga recuperan la selección sin restaurar otra tarjeta durante una transición. Las respuestas abortadas no reemplazan la jornada actual. Sin liga explícita ni selección no se carga un predictor inicialmente; el análisis manual y las estadísticas siguen disponibles.

## Datos y fechas

`GET /api/partidos/agenda?fecha=YYYY-MM-DD&liga=&estado=todos&buscar=&pagina=1&tamano=50` consulta solamente PostgreSQL en READ ONLY. Tamano admite 1–100. Liga: vacío/nba/wnba/euroliga. Estado: todos/pendientes/finalizados. No descarga fuentes ni actualiza calendarios. El timestamp de consulta y el último cambio guardado se identifican como tales, sin afirmar frescura del proveedor.

- NBA y Euroliga solo tienen `fecha_partido` DATE en el catálogo existente. Se conserva el día canónico; no se inventa una medianoche UTC ni se afirma una conversión horaria a Colombia. Las tarjetas dicen Hora por confirmar. Los partidos con hora conocida se ordenan por instante; los demás, por competición/equipo.
- WNBA utiliza el inicio verificado de `fixtures_wnba`/`partidos_fuente_wnba`, convertido a America/Bogota. Un resultado vinculado se muestra una sola vez y conserva el ID estable del fixture. Los fixtures sin hora mantienen su día y su incertidumbre.
- Los ceros de un partido pendiente no se muestran como resultado final. Se excluyen registros canónicos inválidos y fases WNBA ajenas al predictor.

## Consultas históricas

El mismo día o un día anterior, un encuentro sin hora se trata conservadoramente como reconstrucción histórica. Con hora se compara el instante real. Una tarjeta puede abrir un partido iniciado/terminado aunque su estado siga PROGRAMADO. No se modifica el estado para habilitarlo. El reloj de la vista revisa esta condición cada 15 segundos, sin consultar proveedores.

NBA obtiene el partido canónico y valida liga/localía. El refit efímero utiliza el filtro NBA entrenable y `fecha_partido < fecha del encuentro`, con las temporadas solicitadas. Nunca sustituye el artefacto activo, registra versión, consulta calibradores actuales, añade contexto actual ni registra predicciones/bitácora. Requiere 100 finales anteriores y 6 por equipo. Su dispersión es del ajuste retrospectivo y no constituye validación temporal. La regulación es de 48 minutos, sin OT.

Euroliga reconstruye en memoria TRAIN/CAL/EVAL exclusivamente antes del día del partido. Requiere al menos 600 finales anteriores y los mínimos existentes de CAL/EVAL/equipos; puede abstenerse. No publica el refit ni crea journal de esa consulta. Conserva regulación de 40 minutos, sin OT.

WNBA conserva su motor y el alcance temporal existente, permite consultar estados pasados pendientes/en vivo/demorados/suspendidos/cancelados, resuelve fixtures históricos fuera de la ventana móvil y admite el día sin inventar hora. Una fecha futura sin hora no acredita un pronóstico oficial. Las consultas de fixtures pasados no crean journal; se mantiene el journal previo para otros análisis manuales/cortes según su contrato.

La presentación identifica Histórico reconstruido, explica RAW, utiliza Tu análisis, omite sugerencias operativas de apuesta y bloquea guardar/combinadas en históricos. La reconstrucción usa datos hoy disponibles anteriores al corte deportivo; no certifica que cada dato o el algoritmo estuvieran publicados en aquella fecha.

## Verificación local

- 1.752 pruebas backend en PostgreSQL local desechable; cero omitidas. Tres avisos de deprecación existentes.
- 135 pruebas frontend. Lint y TypeScript correctos; build correcto con aviso existente de importación estática/dinámica de WNBA.
- Recorrido real por API e interfaz: Celtics–Bulls, Golden State Valkyries–Atlanta y Žalgiris–ASVEL, en modo histórico y sin botón para guardar apuestas.
- Agenda del 26: 10 registros NBA/WNBA; del 27: 10 NBA/Euroliga. Son registros de la BD, no un calendario completo certificado.
- Móvil 390×844: clientWidth y scrollWidth 382, sin desbordamiento horizontal.
- Conteos antes/después de las consultas reales: partidos 15444, modelos 2190, predicciones 3058, apuestas 199, apuestas_analizadas 636; sin variaciones. Sin nuevas altas de archivos en directorios WNBA/Euroliga auditados.

Evidencias, inventario, preimágenes y parche incremental fuera del repositorio:
`/home/erik-fuentes/Documents/Codex/2026-10-25/ho/outputs/agenda_baloncesto_2026-10-26/`

## Pendientes de operación

Recuperar horas verificadas NBA/Euroliga y revisar sus fechas canónicas frente al día COT; sincronizar calendario y estados/resultados con procedencia y revisiones; mantener ventanas futuras móviles y mostrar cobertura real. Calibración y superioridad predictiva requieren evaluación temporal independiente: no se acreditan por esta mejora de interfaz. No se instalaron tareas periódicas, modificaron fuentes ni publicaron commits.

## Revisión de publicación

Se verificó un candidato aislado del resto del checkout: 1.385 backend sin
omisiones y 132 frontend, lint/TypeScript/build correctos. Estos conteos no son
los 1.752/135 del árbol mezclado citado arriba. Se corrigió una variable histórica
sin inicializar en el análisis manual Euroliga, con regresión; los handlers de
análisis NBA se ejecutan fuera del bucle asíncrono para no bloquear la agenda.
Se incluyen como dependencias las garantías READ ONLY y contexto del pool HTTP.
Esta revisión de la agenda no cierra aún los pendientes de sincronización ni
calibración del prompt maestro, que continúan como bloques separados.
