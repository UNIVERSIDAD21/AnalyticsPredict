# WORK ORDER — Limpieza de documentación y creación de fuente de verdad actual

## Contexto
La carpeta `docs/` del proyecto contiene demasiados archivos `.md` acumulados por iteraciones, tareas y entregables históricos para Borlty. Hoy el problema no es que exista documentación, sino que se está mezclando:

- contexto vigente
- entregables terminados
- instrucciones temporales
- evidencia histórica
- archivos obsoletos o reemplazados

Eso aumenta el ruido, dificulta encontrar la fuente de verdad y eleva el riesgo de que el agente tome como vigente algo que ya no debería gobernar el proyecto.

## Objetivo
Reorganizar `docs/` para que:

1. exista una **fuente de verdad actual** clara y pequeña,
2. los **entregables históricos** sigan disponibles como evidencia,
3. los archivos viejos o reemplazados queden **archivados**,
4. Borlty no vuelva a trabajar sobre contexto mezclado o ambiguo.

## Principios obligatorios

1. **No borrar en bloque** la documentación existente.
2. **No perder contexto útil** ni evidencia histórica.
3. **No dejar archivos activos duplicados** compitiendo entre sí.
4. **No romper enlaces** internos sin dejar redirección o referencia.
5. **No presentar como vigente** un documento que solo fue útil en una fase anterior.

## Estructura objetivo

Reorganizar `docs/` para quedar conceptualmente así:

### 1. `docs/borlty-context/`
Solo debe contener contexto **vigente y activo**, es decir, archivos que hoy sí deben gobernar decisiones.

Debe quedar reducido a pocos documentos núcleo. Como referencia, deberían sobrevivir cosas del tipo:
- índice general activo
- quick start vigente
- estado actual del proyecto
- reglas vigentes de trabajo
- arquitectura/roadmap vigente
- fuente de verdad actual

### 2. `docs/borlty-deliverables/`
Debe contener **entregables y evidencias** ya producidas, por ejemplo:
- auditorías
- validaciones cuantitativas
- deuda técnica priorizada
- mapas de endpoints
- catálogos de KPIs
- reportes de cierre por bloque

Estos archivos no desaparecen, pero ya no deben mezclarse con el contexto activo.

### 3. `docs/archive/`
Debe contener documentación histórica que:
- quedó obsoleta,
- fue reemplazada,
- era una instrucción temporal,
- ya no debe tomarse como prioridad actual,
- o sirve solo como trazabilidad histórica.

### 4. `docs/FUENTE_DE_VERDAD_ACTUAL.md`
Crear este archivo nuevo como **punto de entrada principal** para cualquier trabajo futuro.

Debe responder de forma compacta:
- qué es AnalyticsPredict hoy,
- cuál es el estado vigente,
- qué documento manda,
- qué prioridades están activas,
- qué está en laboratorio,
- qué se considera solo histórico,
- dónde consultar evidencia.

## Regla de clasificación de archivos
Para cada `.md` actual dentro de `docs/` aplicar esta lógica:

### Se queda en contexto activo si:
Todavía debe ser leído por Borlty para tomar decisiones hoy.

### Se mueve a deliverables si:
Es evidencia, auditoría, validación o resultado de un trabajo terminado.

### Se mueve a archive si:
Fue útil, pero ya no debe gobernar el proyecto actual.

### Se elimina solo si:
Es duplicado puro, contradictorio, vacío o claramente reemplazado por otra versión mejor.

## Entregables obligatorios

### 1. Reorganización real de carpetas
Mover archivos a la estructura nueva sin perder contenido útil.

### 2. Archivo nuevo
Crear:

`docs/FUENTE_DE_VERDAD_ACTUAL.md`

### 3. Índice nuevo o actualizado
Actualizar el índice activo para que refleje la nueva estructura.

### 4. Resumen de migración
Crear un archivo corto tipo:

`docs/MIGRACION_DOCUMENTAL_RESUMEN.md`

con:
- qué se movió,
- qué quedó como activo,
- qué quedó archivado,
- qué se eliminó,
- y por qué.

## Criterios de éxito
La tarea se considera bien hecha solo si al final ocurre esto:

1. Un humano nuevo puede entender dónde empieza a leer.
2. Borlty ya no tiene que adivinar cuál `.md` sigue vigente.
3. La documentación activa queda corta, clara y gobernable.
4. La evidencia histórica queda preservada.
5. Lo viejo deja de contaminar decisiones nuevas.

## Restricciones

- No hacer refactor de código en esta tarea.
- No mezclar esta tarea con cambios de backend/frontend.
- No inventar contenido técnico nuevo que no exista; reorganizar y consolidar primero.
- Si detectas documentos contradictorios, priorizar el más reciente y archivar el resto dejando constancia en el resumen de migración.

## Orden recomendado de ejecución

1. Inventariar todos los `.md` actuales en `docs/`.
2. Clasificar cada archivo: activo / deliverable / archive / eliminar.
3. Crear la nueva estructura.
4. Mover archivos.
5. Crear `docs/FUENTE_DE_VERDAD_ACTUAL.md`.
6. Actualizar índice.
7. Crear `docs/MIGRACION_DOCUMENTAL_RESUMEN.md`.
8. Validar que no queden rutas activas ambiguas.

## Instrucción final para Borlty
No trates esta tarea como limpieza estética. Trátala como una tarea de **gobierno documental del proyecto**. El objetivo no es tener menos archivos por verse bonito; el objetivo es que el proyecto vuelva a tener una fuente de verdad clara, auditable y operable.
