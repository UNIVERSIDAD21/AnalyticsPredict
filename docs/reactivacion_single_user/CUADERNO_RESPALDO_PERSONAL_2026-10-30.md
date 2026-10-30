# Cuaderno y respaldo personal — 2026-10-30

## Funciones entregadas

- [x] Respaldo JSON versionado que contiene consultas completas, notas, etiquetas, favoritos de consultas/equipos/ligas/competiciones y apariencia guardada.
- [x] Vista previa antes de incorporar: consultas nuevas, repetidas, conflictos con versiones locales y favoritos nuevos.
- [x] Mezcla conservadora por ID: conserva entradas actuales y sus notas; un conflicto no reemplaza silenciosamente su snapshot.
- [x] Compatible con los respaldos anteriores que contienen un array de entradas del cuaderno.
- [x] Apariencia del respaldo opcional; predeterminadamente se conserva la actual.
- [x] Descarga de copia previa al incorporar. El mensaje acredita preparación de descarga, no almacenamiento físico confirmado por el navegador.
- [x] Validación de versión, estructura, IDs únicos, fechas y capacidad. Archivo de hasta 12 MB; profundidad limitada. Sin truncar entradas para forzar la importación.
- [x] Detección de datos cambiados desde la vista previa y reversión de escrituras completadas si falla una clave posterior de localStorage.
- [x] Rescate literal de las tres claves personales cuando el formato actual está dañado; no se sobrescribe el original.
- [x] Cuaderno con búsqueda por palabras sin tildes, filtros por liga/favoritos/etiqueta/fechas Colombia, ordenación y capacidad visible.
- [x] Apertura por `/cuaderno?entrada=<id>` y acceso desde el aviso de guardado. Vista del resultado cargada bajo demanda y protegida frente a copias incompatibles.
- [x] Estrella de consulta independiente del guardado de notas. No guarda un borrador al cambiar el favorito.

## Uso local

- [x] Abrir Mi cuaderno para buscar y organizar las consultas guardadas en el navegador actual.
- [x] Crear respaldo prepara un archivo JSON: conservarlo fuera del navegador para poder recuperarlo.
- [x] Restaurar archivo lee un respaldo personal v1 o un cuaderno anterior; revisar los conteos y pulsar Incorporar respaldo.
- [x] Las consultas con ID existente conservan su versión local. Para incorporar revisiones de notas de otro respaldo con el mismo ID, revisar/exportar ambas versiones; no hay sobrescritura automática.
- [x] Guardar notas es explícito. Reabrir el resultado conserva su fecha y parámetros; no ejecuta de nuevo el análisis.

## Verificación realizada

- [x] Conjunto frontend completo: 199 aprobadas, 0 fallidas y 0 omitidas, con un worker.
- [x] ESLint, TypeScript y compilación final aprobados.
- [x] Pruebas de round-trip, compatibilidad, conflictos, cambios durante la vista previa, capacidad, corrupción y rollback de escrituras.
- [x] Pruebas de búsqueda con tildes, día de Colombia y ordenación sin mutar el original.
- [x] API/UI compilada reales: consulta técnica del artefacto NBA, guardado, notas/etiquetas/favorito, exportación y restauración del archivo descargado en almacenamiento inicialmente vacío.
- [x] Resultado restaurado con los mismos porcentajes, media, corte y timestamp. No corresponde a un fixture deportivo actual verificado.
- [x] Revisión de la compilación final en escritorio de 1272 px: temas claro/oscuro, búsqueda, favorito y persistencia tras recargar; sin overflow horizontal ni controles de botón sin nombre observados. El cambio de viewport no se aplicó en esta sesión: no se declara verificación móvil real.
- [x] Sin nuevos endpoints de escritura ni cambios de modelos, calibradores, entrenamiento, cuotas del proveedor o BD deportiva.

## Alcance y continuidad

- [x] Código integrado en la copia activa R, conservando HEAD e índice y los cambios preexistentes de Borlty. No se creó un commit que mezcle trabajo ajeno.
- [x] Los backups personales no contienen la BD, modelos, journals de backend ni la Bitácora. No constituyen un respaldo completo de AnalyticsPredict.
- [x] El límite del cuaderno sigue siendo 100 entradas y 4.000.000 de unidades de texto serializado; puede fallar antes si la cuota global del navegador está agotada.
- [x] localStorage no ofrece transacciones de varias claves: se usa rollback ante fallos síncronos y se descarga una copia previa. No se garantiza atomicidad ante cierre abrupto, fallo del disco o escritura simultánea de otra pestaña.
- [x] La restauración exige un estado actual legible. Para datos dañados se ofrece copia de recuperación; no se los reemplaza sin conservarlos.
- [x] Los formatos futuros y respaldos de recuperación literal no se importan como si fueran respaldo personal v1.
- [x] La migración BD continúa en su estado documentado. No se reclasifican las 30 mejoras de Borlty ni se atribuye eficacia predictiva a estas funciones.
