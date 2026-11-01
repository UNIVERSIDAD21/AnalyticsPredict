# Concurrencia HTTP y temporadas — 2026-10-26

## Estado

Corrección local aplicada al servicio de desarrollo. HEAD sigue `80ca327`;
sin commit/push/despliegue remoto ni CI nueva. Se preservaron los diffs anteriores.

## Causas comprobadas

- Un proceso atendía rutas `async def` con psycopg, archivos y cálculo síncronos.
  Una espera bloqueaba el bucle compartido: incluso `/salud` no respondía en 5 s.
- Estadísticas hacía una consulta por cada equipo activo, además del catálogo:
  81 consultas en las dos temporadas contrastadas. Repetirlo por ventana saturaba
  las cinco conexiones. Quitar solo el bloqueo del bucle no bastó: 20 ventanas
  simuladas dieron 77/100 respuestas correctas antes de la optimización adicional.
- El cliente serializaba listas como `equipo_ids[]`, mientras FastAPI espera
  parámetros `equipo_ids` repetidos. Las solicitudes obsoletas de temporadas no
  se cancelaban al cambiar la selección.
- La creación perezosa del pool no estaba protegida para llamadas concurrentes;
  no había límites explícitos de conexión/TCP ni de consultas HTTP en ese pool.
  Este último riesgo se corrigió; no se atribuye a él el bloqueo inicial sin traza.

## Implementación

1. 99 operaciones HTTP síncronas en 18 módulos usan `def`: FastAPI las ejecuta
   en su pool de hilos. Los agregadores llaman a las mismas funciones síncronas.
   Salud permanece asíncrona y ligera. Se conservaron contratos y cálculos.
2. Singleton del pool protegido por lock, máximo cinco conexiones. Espera de
   adquisición 8 s, conexión 5 s y TCP user timeout 15 s/keepalives. Por conexión
   HTTP: statement_timeout 15 s y lock_timeout 5 s, locales a la transacción.
   GET/HEAD siguen READ ONLY; ni esa protección ni los límites contaminan POST
   o tareas explícitas fuera de HTTP. Los timeouts no se envían como opciones de
   startup, incompatibles con el pooler transaccional usado.
3. Estadísticas obtiene todos los partidos del alcance en una consulta y los
   agrupa en memoria por ambos equipos, conservando filtros, FT/OT, orden y reglas
   de tiebreaker existentes. Sin cambio del alcance ni ajuste de modelos.
4. `compartir_lectura`: equipos, temporadas, estadísticas y próximos NBA comparten
   únicamente llamadas iguales simultáneas. Clave por argumentos, copias separadas,
   limpieza tanto ante éxito como error. No TTL, respuesta histórica almacenada,
   repetición automática ni deduplicación de POST/análisis.
5. Temporadas envía parámetros repetidos y AbortSignal NBA/WNBA; al cambiar
   selección o salir se cancela la solicitud anterior. No se reemplaza una
   selección reciente con una respuesta tardía. Timeout general del cliente
   **permanece en 30.000 ms**; mensaje legible y cancelación sin error técnico.

## Verificación

- 1.669 backend aprobados, 0 omitidos, PostgreSQL 16 sintético propio. Tres avisos:
  Starlette/httpx y dos usos preexistentes de utcnow, uno expuesto por la nueva prueba.
- 116 frontend; lint/build/diff check aprobados. Aviso Vite de WNBA estática/dinámica
  preexistente; no se cambiaron dependencias.
- Siete análisis lentos sintéticos retenidos simultáneamente, mientras salud y
  temporadas responden; sin POST productivo. Singleton con 40 llamadas simultáneas,
  deduplicación/copia/recuperación, parámetros de temporada, límites de transacción,
  SQL agregado y OT cubiertos por siete pruebas backend nuevas.
- Equivalencia READ ONLY bajo snapshot REPEATABLE READ: todos los campos de
  estadísticas exactos en 2026–2027 (20 equipos con muestra) y 2020–2021 (30).
  Consulta explícita por temporada: 81→2 SQL. Tiempo observado 6,80→0,17 s y
  6,89→0,36 s, respectivamente. No es un SLA ni evaluación predictiva.
- Carga HTTP GET real: 7 ventanas simuladas, 35/35 respuestas 200, máximo 1,1556 s;
  20 ventanas, 100/100, máximo 1,3083 s. Incluye equipos, estadísticas, próximos,
  temporadas de dos equipos y salud, sin escritura ni fitting.
- Siete pestañas del navegador propio abiertas conjuntamente: Boston–Atlanta,
  nueve temporadas cargadas, cero errores visibles/JS y sin overflow observado.
  Captura auténtica y métricas de recursos archivadas. No se enviaron análisis.

## Operación y límites

La aplicación local fue reiniciada porque el proceso anterior estaba atascado y
no completaba la recarga. Backend/frontend quedaron activos en loopback 8000/5173.
No se detuvieron scrapers ni el PostgreSQL ajeno 55432. PostgreSQL sintético propio
55439 detenido al terminar. Navegador del Jefe intacto.

No hay un límite impuesto de siete ventanas. La evidencia cubre los escenarios
anteriores, no un número ilimitado ni cálculos predictivos productivos ilimitados
simultáneos. Un fallo real de red/BD sigue produciendo un error acotado; no se
oculta con esperas infinitas, resultados viejos ni reintentos de escrituras.

Las lecturas no se usaron para ingestar, entrenar, resolver pronósticos, modificar
apuestas o activar/calibrar modelos. La reparación histórica de 99 filas no se repitió.

Entrega externa: `CONCURRENCIA_MULTIVENTANA_2026-10-26`, con código completo,
diff incremental, pruebas, carga, equivalencia, captura e integridad SHA-256.
