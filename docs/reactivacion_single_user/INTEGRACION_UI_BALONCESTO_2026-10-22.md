# Baloncesto: NBA y Euroliga en una pantalla — 2026-10-22

## Uso

Abrir `/baloncesto` y elegir **Liga: NBA o Euroliga**. La navegación principal y el
acceso del dashboard se llaman **Baloncesto**. La liga queda en la URL
(`/baloncesto?liga=nba` o `?liga=euroliga`) y se conserva al recargar, compartir y
usar atrás/adelante. Los enlaces `/app` y `/euroliga` redirigen a esa misma pantalla;
el primero conserva también los parámetros antiguos de estadísticas/equipo.

Se reutilizan el formulario del analizador NBA, el selector de partido, los
selectores de equipos y mercados, el control de línea Over/Under, los botones,
el estado vacío, la tarjeta de probabilidades y el layout de panel izquierdo/resultados. No se incrusta la
pantalla independiente anterior de Euroliga.

## Aislamiento y diferencias necesarias

- Cada liga monta solo su módulo. Al cambiarla se descartan formulario, errores y
  resultados transitorios de la otra; un resultado no se convierte entre motores.
- NBA mantiene su API, estadísticas, temporadas y comportamiento de análisis.
  El calendario NBA continúa filtrado por competición.
- Euroliga usa únicamente `/api/euroliga/*`. No consulta temporadas NBA ni envía
  cuotas, calibradores, IDs de modelos o selecciones de temporadas al motor Euro.
- El contrato TypeScript del formulario distingue ambas peticiones. La petición
  Euroliga contiene equipos, fixture opcional, mercado, línea y parciales por cuarto.
- El selector compartido explica el historial real de Euroliga: cada ejecución se
  conserva, incluso sin fixture. No promete entrenamiento ni comparación automática.
- Euroliga conserva regulación de 40 minutos sin OT, ventaja de puntos (no
  moneyline), probabilidades RAW y condicionamiento a Q1–Q3 completos. Los controles
  no soportados por su API no se presentan como funcionalidades existentes.
- Su pestaña de estadísticas informa la muestra histórica del predictor y su
  elegibilidad; no se hace pasar por una tabla de medias de temporada NBA. Forma
  reciente y H2H siguen en el resultado Euro.
- El historial reabre el JSON original sin repetir POST. Las pestañas no borran el
  formulario ni provocan recálculos. Cambiar sus parámetros invalida la salida visible.

La adaptación del catálogo Euro no inventa abreviaturas NBA. `buscarEquipo` rechaza
una búsqueda vacía antes de comparar abreviaturas: evita seleccionar silenciosamente
el primer club de un catálogo que carece de ellas.

## Verificación

51 pruebas frontend aprobadas (incluidas navegación real, redirecciones, atrás/
adelante, limpieza al cambiar liga, payload Euro exacto, ausencia de consultas NBA,
validación de equipos y parciales, invalidación de salida e historial sin otro POST).
Lint, compilación de producción y auditoría de dependencias de producción aprobados. Las peticiones POST se prueban con
servicios simulados; **no se ejecutaron análisis productivos** para esta integración.

Revisión visual con datos reales en navegador administrado: NBA y Euroliga,
selección/autocompletado del fixture, catálogo propio y reapertura de la captura
Euro anterior. Escritorio 1440 px y móvil 390 px sin desbordamiento horizontal.
Se conserva la fecha original de la captura histórica; no es un análisis nuevo.
La conexión con el navegador habitual agotó timeout dos veces; no se reinició ni
alteró ese navegador. Se utilizó el perfil de pruebas para la inspección.

Sin cambios de backend, base de datos, entrenamiento, modelos, calibración,
cohortes o apuestas. No se repite la suite backend local por un cambio exclusivamente
frontend; el CI conserva sus controles de backend/PostgreSQL/Compose. La eficacia
científica sigue **NO_CERTIFICADA**; unificar la interfaz no iguala el rendimiento.

Evidencia externa: `INTEGRACION_BALONCESTO_NBA_EUROLIGA_2026-10-22/`, con logs,
capturas auténticas, comprobación de hashes, acta y estado de publicación/CI.
