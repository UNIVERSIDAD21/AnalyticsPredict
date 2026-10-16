# KPI/P&L residual y auditoría GET — 2026-10-16

## Alcance y contrato vigente

Cierre técnico de los consumidores activos M04 y de lecturas/observabilidad M05;
no certificación del histórico ni cierre del plan global. Calibración NBA mantiene
su [contrato de series, muestras y versión](KPI_CALIBRACION_2026-10-16.md).
No se crean vistas físicas propuestas sin consumidor, modelos ni calibradores.

El propietario confirmó que no existen soportes originales de los importes.
`servicios/politica_pnl.py` gobierna resumen global/cortes por deporte y mercado,
estadísticas NBA, métricas NBA por mercado/confianza/mes, listado/resumen,
rendimiento y serie temporal fútbol, y resumen ejecutivo fútbol.

- `roi`, ganancias y stakes **agregados** son `null`/N/D sin procedencia y unidad.
  Ni una suma aritmética ni una fila conciliable acreditan su origen.
- `calidad_pnl`: estado, n resueltas/evaluables/excluidas, motivo
  `SOPORTES_ORIGINALES_NO_DISPONIBLES`, unidad desconocida, grano APUESTA y corteUTC.
  El diagnóstico aritmético/deportivo previo no se convierte en certificación.
- Conteos/resultados/win rate siguen siendo **registrados**, no eficacia validada.
  Los importes individuales y las filas históricas se conservan sin DML.
- NBA/fútbol/combinadas se agregan una vez por apuesta, sin multiplicar por
  selecciones/predicciones. Los mercados se segmentan también por deporte.
- Listado y resumen fútbol comparten filtros antes de paginar, incluido el día
  final completo. La serie temporal declara acumulación dentro de la ventana y n
  acumulada; una ventana vacía no representa ROI cero.
- Metadatos de columnas se leen sin TTL. Se respetan `resultado`, `ganancia` y
  `creado_en` canónicos y alternativas verificadas, incluido el enum de fútbol sin
  `ANULADA`. No se inventan columnas ni se modifica ese enum.

## Lecturas y fallos

`LecturasHTTPMiddleware` conserva un ContextVar GET/HEAD durante la respuesta,
stream y tareas asociadas, incluido el threadpool síncrono. `PoolAplicacion`
presta conexiones en READ ONLY y restaura su estado antes de devolverlas al pool.
POST/CLI explícitos no heredan el estado de otra petición. No cambia roles,
políticas globales ni permisos de BD. No es una barrera frente a código hostil
que use conexiones ajenas o desactive deliberadamente la protección.

Se retiró la escritura de telemetría de contrato fútbol desde el serializador y
el TTL de columnas. Bitácora ya era de lectura. CSV se construye en memoria.
Los dos consumidores del calculador de calibración pasan `persistir=False`;
el método de persistencia sigue disponible únicamente para operaciones explícitas.
Serving/Estado cargan artefactos y snapshots sin entrenar, resolver ni ingestar.

Fallos de BD/configuración no se ocultan como listas vacías o HTTP200 de éxito:
partidos, estadísticas, alertas/calibradores y calidad propagan el fallo. Modelos
no disponibles devuelven503; salud puede describir un proceso degradado. Errores
5xx se sanitizan, con trace_id y contador HTTP, también con DEBUG; intentos de
escritura bloqueados tienen contador propio. Se mantienen cabeceras CORS.
Errores técnicos persistidos en jobs no se exponen literalmente.

Incidencias encontradas en la comprobación: UUID real del driver en auditoría
fútbol, límite Query omitido al invocar el resumen ejecutivo, ruta estática de
telemetría oculta por UUID y referencias a columnas legacy en madurez. Corregidas.
La adaptación de madurez conserva la política existente de probabilidad efectiva
(calibrada solo con ID, si no raw) y **no cambia sus umbrales ni promueve mercados**.
Su validación científica por versión/cohorte sigue en M12.

## Auditoría y evidencia

Inventario: **78 GET efectivos de OpenAPI**, no solo decoradores directos.
Revisión de raíces y llamadas locales transitivas, SQL, despacho de modelos,
lecturas de archivos, exportaciones y ramas de persistencia. El grafo estático
es conservador: incluye la rama de persistencia inalcanzable con `persistir=False`
y no resuelve por sí solo todo despacho dinámico; se contrastó con código y ejecución.

Evidencias completas fuera del producto:
`KPI_PNL_Y_AUDITORIA_GET_2026-10-16`, en la carpeta de entregas del propietario:
grafo por ruta, matriz HTTP y revalidaciones, huellas y logs, pruebas y acta/CI.
Resultado consolidado:74 respuestas200 y4respuestas404 esperadas (tres jobs
ausentes y explicación con feature desactivada), sin5xx/422 pendientes. Los errores
intermedios y las revalidaciones se conservan en los logs. No confundir un404 esperado por ausencia de job o feature desactivada con un200
funcional. Ejercitar una ruta no prueba todas las combinaciones de sus parámetros.

**814pruebas backend**, cero fallos/skips, dos deprecaciones heredadas;
**29pruebas frontend**, lint/build aprobados. Pruebas PostgreSQL sintéticas verifican fórmulas cross-sport, cohorte/paginación,
N/D, cambios sin TTL, ausencia de multiplicación por selecciones, enum realista,
protección GET/HEAD tras COMMIT, reutilización de conexiones y concurrencia POST.
API y componentes/adaptadores frontend conservan N/D y resultados registrados.
El contraste ASGI real usa guardas READ ONLY y un audit hook que rechaza mutaciones
de archivos/procesos; compara19 huellas de tablas y archivos de datos/modelos/config.
No es una revisión visual, ni prueba de rendimiento futuro, ni una ingesta.

## Límites que permanecen

P&L sin soportes: no recuperable controlado, no una tarea pendiente del propietario.
M12 científico/confidence/odds, fuentes independientes/por tiempos, outcomes
prospectivos, visual y H4/H12 residuales siguen abiertos. Sin cron, notificaciones,
DDL/DML productivo, entrenamiento, activación ni nuevas capturas en este bloque.
