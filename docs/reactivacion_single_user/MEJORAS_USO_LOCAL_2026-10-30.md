# Mejoras de uso local — inicio de implementación, 2026-10-30

Orden del propietario: iniciar el catálogo completo L01–L30 de la revisión del
29 de octubre. **Primera entrega funcional, no cierre de las treinta mejoras.**
Desarrollo local sin lanzamiento comercial, despliegue ni activación de modelos.
La migración continúa pendiente: no existe una BD de aplicación restaurada y
verificada en Windows. La fuente identificada sigue rechazando por cuota el30oct.

## Uso

- `/hoy`: resumen de las agendas existentes, fecha Colombia y filtro por liga;
  acceso a la ficha sin volver a elegir equipos/localía. Fallos por dominio N/D,
  no cero. Vista resumida; la agenda completa conserva búsqueda/paginación.
- `/base-local`: consulta NBA del artefacto sin BD, contexto, cuotas, fitting,
  registro de predicciones ni apuestas. Q1–Q4/total48min sin OT, RAW. No verifica
  fixture ni resultado actual. Muestra versión, corte, dataset y muestra de ajuste.
- `/cuaderno`: copias de consultas cross-liga, notas, etiquetas y favoritos de
  **análisis**, más equipos/ligas/competiciones separados. Al reabrir no se repite un POST. Se guarda
  en este navegador, no en BD; no equivale a respaldo fuera del equipo.
- `/laboratorio`: inventario de artefactos cargables y evaluación de desarrollo
  ya contenida en ellos. No mide nuevamente ni asigna esas métricas a los refits.
- Temas claro/oscuro, densidad/tamaño recordados, fuentes del sistema, foco visible,
  salto al contenido y movimiento reducido. Las rutas anteriores se conservan.
- Resultados compartidos: guardar consulta separado de guardar apuesta, JSON/CSV
  y versión imprimible. Se conserva el snapshot, advertencias y selección original.

### Iniciar sin BD

Con las dependencias de `backend/requirements.lock` instaladas en una venv y
`npm ci && npm run build` ejecutados en `frontend`:

```powershell
& .\backend\.venv\Scripts\python.exe .\scripts\iniciar_local.py --estado '<directorio existente de artefactos>'
```

Linux usa el Python de su venv. `--estado` contiene `modelo_nba_activo.npz` y,
si existen, `euroliga/activo.json` y `wnba/activo.json`. No copiar credenciales
a ese directorio. También se admiten las rutas protegidas de artefacto por entorno.
`--comprobar --sin-abrir` verifica y cierra su propio arranque. Usa loopback8000/5173;
si están ocupados corta sin detener/reutilizar procesos ajenos. Ctrl+C cierra solo
esta ejecución. No instala servicios, inicia entrenamientos ni sincroniza fuentes.

El modo predeterminado establece `ANALYTICSPREDICT_SOLO_BASE_LOCAL=1`: `obtener_pool`
rechaza antes de crear el pool y el POST de sincronización se bloquea. No es un
sandbox general ni un modo sin Internet del navegador. `--con-bd` exige una
configuración PostgreSQL loopback en `backend/.env`; **no sustituye** restauración,
conciliación ni verificación de migración. No se ejecutó aquí contra BD de producto.

## Contratos y compatibilidad

- Consulta NBA PRE usa exclusivamente `obtener_modelo()`. Enviar `temporadas`
  fuera de una reconstrucción histórica produce422, no un ajuste oculto ni un
  filtro ignorado. UI ya no envía ni consulta temporadas para NBA PRE. WNBA conserva
  sus alcances propios; los cortes completos y reconstrucciones siguen separados.
- El entrenamiento/publicación explícitos existentes se conservan. No se ejecutaron.
- Metadatos y muestras ausentes son N/D. La confianza existente se identifica como
  heurística, no fiabilidad. La explicación no añade contribuciones18/12,100casos,
  70%acierto, medias iguales a líneas ni intervalos fijos. Campos sin soporte son
  null/listas vacías; se actualizó su consumidor. El feature flag no se activó.
- Consulta base solo da probabilidades en líneas terminadas en.5. Enteras y otras
  fracciones: media/desviación conservadas, probabilidad/push N/D con motivo. No se
  atribuye una masa discreta de push inexistente al artefacto normal continuo.
- Comparador base reutiliza media/desviación originales, con CDF aproximada
  (error absoluto<1e-6), explícitamente distinta de una nueva salida del predictor.
  La probabilidad de la línea original se conserva exactamente desde la API.
- Locks Windows `msvcrt` y POSIX `flock`, exclusión no bloqueante entre procesos;
  no borrar locks ni deshabilitar hashes. JSON UTF-8 explícito en loaders/journals,
  publicación WNBA y CLIs intervenidos. Tildes/hashes conservados.
- Publicadores/script `fchmod` solo POSIX. Windows usa ACL heredadas, no afirma0600.
  WNBA sincroniza el archivo antes de reemplazarlo; no hace `fsync` de directorio
  con `os.open` en NT ni promete su misma durabilidad POSIX ante corte eléctrico.
- POST explícito de sincronización Windows solicita una ejecución puntual del
  runner existente, sin shell, consola visible, timer ni handles de salida heredados.
  No se invocó con fuentes/BD reales. GET/render no arranca ese proceso.
- Contexto NBA: retirado LRU persistente que no tenía revisión común de dataset;
  se relee en cada consulta. Evita contexto viejo tras ingestas; no se presenta como
  un benchmark de mejora de latencia ni como versionado de dataset ya implementado.

## Seguimiento del catálogo completo

Implementada significa código y comprobaciones del alcance descrito, no eficacia
deportiva certificada ni E2E de todas las pantallas con BD real.

| ID | Estado de esta entrega | Límite o siguiente paso |
|---|---|---|
| L01 | Implementada | Compatibilidad de rutas intervenidas; operación real de sincronización no ejecutada |
| L02 | Implementada | UTF-8 de artefactos/journals/CLIs intervenidos; no conversión de archivos originales |
| L03 | Implementada | PRE no ajusta/crea versiones; entrenamiento solo explícito |
| L04 | Implementada | Sin factores/muestras/intervalos inventados; completar con evidencia real, no defaults |
| L05 | Parcial | Contrato claro en base local; revisar contratos legacy enteros/OT por separado |
| L06 | Parcial | Laboratorio expone comparaciones originales; falta nuevo benchmark NBA emparejado |
| L07 | Pendiente de datos | Recencia/forma causal NBA: snapshot elegible y protocolo antes de medir |
| L08 | Pendiente de datos | Errores fuera de muestra y covarianza por candidato/objetivo |
| L09 | Pendiente de evidencia | CAL/TEST y cohorte futura suficientes; ninguna calibración activada |
| L10 | Bloqueada por originales | Recuperar desarrollo/cohorte V4 corregidos y outcomes; no sustituirlos |
| L11 | Pendiente de benchmark | Euro: comparación temporal nueva, no heredar evaluación del refit |
| L12 | Parcial | WNBA evaluada: CAL eligió k0, sin mejora; fallback no activado. Euro aún sin snapshot |
| L13 | Pendiente de datos | Conteos fútbol por competición/familia y disponibilidad causal |
| L14 | Pendiente de inventario | Cobertura vigente y preferencias de uso; no llenado automático de gaps |
| L15 | Implementada | Trazabilidad común NBA/Euro/WNBA/fútbol y base local; datos no conservados N/D |
| L16 | Implementada | Hoy reutiliza agendas, enlace a ficha y estados parciales; BD real pendiente |
| L17 | Implementada | Base visual sobria y preferencias; quedan componentes legados con colores propios |
| L18 | Implementada | Fichas baloncesto/fútbol progresivas; agenda y seguimiento separados de configuración |
| L19 | Implementada | Favoritos de consultas, equipos, ligas/competiciones; notas/etiquetas y almacenamiento aislado |
| L20 | Parcial | NBA base continua y Euro discretizada sin API; WNBA Sobol/OT y fútbol no se aproximan como normales |
| L21 | Implementada | Snapshots/exportación/reapertura; no importador de respaldos del cuaderno |
| L22 | Implementada | NBA local real, corte visible y bloqueo explícito de BD; no offline con contexto |
| L23 | Implementada | Error no equivale a cero; fuentes ausentes N/D en superficies intervenidas |
| L24 | Parcial | Teclado/foco/reduced-motion y pantallas verificadas; auditoría exhaustiva pendiente |
| L25 | Implementada | CI Windows, UTF-8 real y fixture futura sin fecha de caducidad fija |
| L26 | Implementada | Relectura conservadora sin LRU; no clave de revisión inventada |
| L27 | Parcial | Cálculo base extraído a servicio; no reescritura de rutas monolíticas |
| L28 | Implementada | Lanzador propio no destructivo y modo base; no comprobante de migración |
| L29 | Pendiente de diseño/datos | Live por reloj/posesiones exige fuente temporal y evaluación nuevas |
| L30 | Pendiente de fuentes | Lesiones/alineaciones/xG con cobertura y disponibilidad acreditadas |

**15 implementadas,6 parciales,9 pendientes/bloqueadas.** El catálogo permanece
abierto. No se presentan las seis parciales como funcionalidades completas.
[Continuación, experimento WNBA y límites](CONTINUACION_MEJORAS_2026-10-30.md).

## Protocolo de continuación científica

Antes de nuevos ajustes: snapshot identificado/hash, partidos elegibles y ausentes
por objetivo, cortes TRAIN/selección/dispersión-CAL/EVAL sin dividir simultáneos,
baseline y variantes predeclaradas, denominador completo y recursos acotados a un
proceso/hilo. Las features anteceden al outcome y no consumen finales futuros.
NBA: identidad actual vs recencia vs forma; incertidumbre/covarianzas de errores
fuera de muestra. Evaluar MAE/RMSE/sesgo, Brier/logloss con definición, coberturas
50/80/95 y anchura, abstenciones y soporte de equipos. No seleccionar en EVAL.

Conservar separados candidato seleccionado, refit final y evidencia prospectiva.
CAL de residuales no implica calibración probabilística. Ninguna promoción por
tests, esfuerzo invertido o MAE retrospectivo. WNBA ya usa recencia: evaluar mejoras
incrementales, no presentarla como inexistente. Euro/WNBA/fútbol no heredan pesos,
calibradores ni eficacia NBA. V4 solo se evalúa desde su cohorte original.

## Validación de esta entrega

- 363 backend aprobadas/0 omitidas con PostgreSQL18 sintético exclusivo en55434;
  solo datos de fixtures, bases/esquemas propios eliminados y cluster detenido.
  No se usaron los servicios5432 ni55433 ni datos de aplicación.
- Control adicional sin BD:354aprobadas/8omitidas, cero intentos de red Python
  bloqueados; socketpair interno de asyncio Windows permitido expresamente.
- 143 frontend aprobadas, lint/TypeScript/build aprobados. Dos workers para el host.
- API y UI compilada reales con artefactos publicados:6vistas, escritorio1366 y
  móvil390,0erroresJS/0overflow. Una consulta técnica arbitraria sin fixture;
  comparar/guardar/reabrir no repite POST. No análisis deportivo de partido real.
- 38archivos de estado antes/después idénticos; no modelos/journals/cohortes alterados.
- Lanzador real inicia/comprueba/cierra sus procesos. No deja servidores de pruebas.
- No certifica eficacia, sincronización productiva, migración ni E2E con BD deportiva.

Evidencias/actas/manifiesto externos a producto en
`IMPLEMENTACION_MEJORAS_USO_LOCAL_2026-10-30`. Rama/publicación y SHA exactos constan
en su recibo, sin incorporar configuración o memoria de OpenClaw al repositorio.
