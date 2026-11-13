# Tablero de actualización de ligas

## Uso

`/actualizaciones` reúne el estado del actualizador manual. En la instalación
habitual se conserva el acceso existente **Actualizar ligas**. Las agendas de
baloncesto y fútbol muestran un resumen compacto y un enlace al tablero.
La rama publicable anterior no incluía esa página: incorpora su ruta y acceso
**Datos**, sin retirar navegación existente.

El resumen separa cuatro indicadores: competiciones diarias con incidencias de
resultados/estadísticas; eventos pendientes de agenda; campos ausentes de fútbol
en la ventana; y última actualización integral completa acreditada. Los valores
proceden del GET existente, no del texto pegado ni de constantes de la interfaz.

## Lectura del detalle

- Una fila por código exacto de competición combina agenda, resultados y cortes.
- El filtro inicial incluye cualquier pendiente de agenda, resultados o cola
  estadística. Su número no equivale al indicador de incidencias diarias.
- Búsqueda local, filtro por deporte y ámbitos diario/archivado no consultan ni
  actualizan las fuentes deportivas.
- Al abrir una fila se distinguen estadísticas faltantes en ventana, cola
  acumulada, campos elegibles, próximo reintento manual, fuentes y motivos.
- Sin finales o sin eventos publicados no significa competición archivada.
  Se usa la clasificación explícita del contrato; no se inventa cobertura.
- Los modelos se muestran aparte, con versión, corte y finales posteriores.
  Actualizar datos no reentrena, activa ni certifica un modelo.
- Carga inicial, errores, datos anteriores tras un fallo, calidad pausada y
  ejecución en curso conservan sus límites. Los datos ausentes aparecen N/D.

## Acciones

**Consultar estado** hace GET `/api/agendas/sincronizacion`. **Actualizar todas
las ligas** conserva el POST manual `/api/agendas/sincronizar`, bloqueado sin
lectura inicial, durante la solicitud/ejecución y ante pausa de calidad. Se
impide la solicitud simultánea por doble clic. El sondeo GET solo acompaña una
ejecución que ya está solicitada o en curso; no programa nuevas actualizaciones.

## Validación y entrega

Pruebas de contrato visual, estados, filtros y acciones con HTTP simulado;
TypeScript, ESLint, compilación y revisión de escritorio/móvil. Se valida también
un ensamblado de la interfaz habitual, conservando rutas, preferencias y funciones
locales que no pertenecen al dashboard. Los resultados exactos, capturas y recibos
de publicación/instalación se conservan fuera del producto en
`Carpeta de Entregas de Borlty/Dashboard_Actualizacion_Ligas_2026-11-13`.

Esta entrega es de interfaz. No acredita una nueva ingesta, cobertura oficial
íntegra, corrección de los pendientes, entrenamiento ni ejecución del ciclo.
