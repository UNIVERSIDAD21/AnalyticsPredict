# Arquitectura de Bitácora Única — Contrato Canónico y Transición

Fecha: 2026-03-31
Estado: ACTIVO (transición controlada)

## 1) Fuente de verdad de la bitácora

### Fuente de verdad canónica (lectura producto)
`GET /api/bitacora/unificada` será la **fuente de verdad canónica de lectura** para la experiencia de bitácora del producto.

Este endpoint consolida registros de:
- `apuestas` (NBA/base)
- `apuestas_futbol` (fútbol)
- `apuestas_combinadas` (combinadas)

## 2) Unificación: lectura vs escritura

### Lectura
Se unifica **desde ya** en el contrato canónico de bitácora unificada.

### Escritura
La escritura se mantiene temporalmente por dominio:
- NBA/base escribe en `apuestas`.
- Fútbol escribe en `apuestas_futbol`.
- Combinadas escribe en `apuestas_combinadas`.

Decisión: no crear una capa de escritura única apresurada para evitar riesgo de regresión en flujos de análisis que hoy son distintos por deporte.

## 3) Contrato canónico final (bitácora)

### Endpoint
`GET /api/bitacora/unificada?version=v2`

### Campos mínimos de registro
- `id`
- `deporte` (`baloncesto|futbol`)
- `tipo_apuesta` (`SIMPLE|COMBINADA`)
- `mercado`
- `equipo_local`
- `equipo_visitante`
- `fecha_partido`
- `resultado`
- `stake`
- `cuota` / `cuota_total`
- `ganancia`
- `confianza_sistema`
- `valor_esperado`
- `creado_en` / `actualizado_en`

### Filtros canónicos
- `deporte`
- `mercado`
- `resultado`
- `tipo_apuesta`
- `desde` / `hasta`
- `confianza`
- `busqueda`
- `orden`
- `pagina` / `tamano`

### Resúmenes canónicos
`GET /api/bitacora/resumen` incluirá:
- resumen global (`total_apuestas`, `pendientes`, `cerradas`, `ganancia_total`, `winrate`, `roi`)
- agregado por deporte
- agregado por mercado

## 4) Convivencia temporal con legacy

- Se mantiene compatibilidad de contratos `legacy|v2` durante transición.
- Las rutas históricas de fútbol para bitácora quedan **deprecadas** como punto de entrada de UX (`/futbol/bitacora`), redirigiendo a `/bitacora`.
- Backend conserva endpoints por dominio para no romper operaciones existentes mientras se consolida la lectura canónica.

## 5) Estrategia de migración

### Fase de transición (actual)
- Unificación de lectura + filtros + resúmenes en `/api/bitacora/*`.
- Escritura por dominio intacta.

### Fase objetivo (posterior controlada)
- Evaluar `POST /api/bitacora` canónico para escribir eventos de bitácora con `deporte` explícito.
- Adaptar módulos de análisis para usarlo sin romper su lógica interna.
- Retirar gradualmente escrituras directas por dominio cuando exista paridad funcional y pruebas de no-regresión.

## 6) Criterio de producto

Se prioriza continuidad de usuario (bitácora única) sin mezclar pantallas operativas de análisis entre deportes.
