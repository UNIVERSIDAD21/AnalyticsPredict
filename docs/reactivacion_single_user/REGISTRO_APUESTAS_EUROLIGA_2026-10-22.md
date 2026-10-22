# Cuota y registro de selecciones Euroliga — 2026-10-22

## Cambio

La salida de análisis Euroliga con una selección Over/Under válida ahora permite
abrir **Guardar en Bitácora**. En el modal se ingresa la cuota decimal observada
(mínimo 1,01) y el stake; el predictor no consulta cuotas ni las incorpora a su
cálculo. El registro usa la línea y el lado elegidos, partido/fecha disponibles y
la competición `euroleague`.

La fila queda en `apuestas`, junto al resto de baloncesto, con `competicion_id` y
`competicion_nombre`; el listado unificado la identifica como `EURO`. El servidor
resuelve la competición y valida que un fixture asociado pertenezca a esa liga;
para Euro también comprueba equipos, localía y fecha antes de insertar.

Se guarda la probabilidad RAW que corresponde al lado y mercado seleccionados,
indicada como no calibrada, y metadatos de análisis/modelo/dataset en la trazabilidad.
Confianza y valor esperado permanecen NULL/N/D; no se asigna confianza ni se calcula
EV automáticamente a partir de la cuota ingresada. La cuota sí permite calcular la
ganancia al conciliar un resultado, pero este cambio no añade resolución automática
Euro. El resolvedor existente sigue limitado a NBA para no usar puntos con OT en una
competición cuyo mercado completo se define a 40 minutos de regulación. Las métricas
y estadísticas NBA también excluyen registros identificados como Euroliga; las filas
históricas sin competición asignada conservan el tratamiento NBA anterior.

## Validación y límites

- UI sintética: análisis → selección Over/Under → cuota `1.91` y stake → llamada del
  servicio a Bitácora, con payload de Euroliga y trazabilidad de origen.
- API sintética: inserción simulada conserva competencia/cuota/probabilidad RAW y
  NULLs analíticos; fixture de otra competencia se rechaza sin inserción. También
  se cubre el caso con probabilidad no disponible.
- Esquema consultado en una transacción READ ONLY: las columnas de competencia existen
  y `probabilidad_sistema`/`confianza_sistema` permiten NULL. No se creó una apuesta.
- Backend focalizado: 8 aprobadas, 9 omitidas por fixture PostgreSQL desechable no
  disponible en el entorno local; suite frontend completa 65/65, ESLint y
  compilación/build aprobados.
- Smoke GET local: salud, frontend y contrato OpenAPI HTTP 200. El navegador no
  tenía pestañas abiertas; no se emitió el POST de análisis productivo que puede
  escribir journal, así que el modal no se verificó en navegador real.
- No hubo POST productivo, escritura/DML, cambio de modelos, entrenamiento ni cuotas
  descargadas. El análisis Euroliga continúa NO CERTIFICADO.
