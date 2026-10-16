# Operación local y prospectiva — 2026-10-15

Estado técnico separado del rendimiento: **NO CERTIFICADO**. Sin notificaciones,
cron, autoentrenamiento ni resolución implícita en GET/startup.

## Uso local

Desde la raíz: `AUTO_KILL_PORTS=false bash scripts/dev.sh`.
Dashboard: `http://127.0.0.1:5173/dashboard`; estado: `/operacion`.
`GET /api/operacion/estado` abre transacción read-only y muestra dominio/frescura,
artefacto NBA, último job, capturas fútbol y conteos prospectivos. Un fallo de BD
es 503, no un conjunto de ceros. Almacén ausente es N/D, distinto de cero capturas.
La fecha sin hora NBA no se convierte a una fecha anterior en UTC−5.

## ML fútbol: actualización técnica posterior

La persistencia/recarga está implementada sin entrenar en serving. El diagnóstico
por defecto usa `scripts/entrenar_futbol.py` sin flags de escritura. Registro,
artefacto y carga se distinguen; no hay versión fútbol activa en el corte real.
Ver `PERSISTENCIA_ML_FUTBOL_2026-10-15.md` para familias, ventanas, comandos,
codec, resultados y límites. No reutilizar calibrador de otra versión ni interpretar
MAE de ajuste como validación temporal.

## Rutina manual explícita

Usar `backend/.venv/bin/python`; no copiar la configuración protegida al terminal.
Los comandos siguientes se ejecutan desde `backend/`. Guardar salidas fuera del repo.

1. Consultar `/api/operacion/estado`. Revisar fuentes/fecha antes de interpretar datos.
2. NBA: ` .venv/bin/python scripts/actualizar_partidos_nba.py --days-back 3 --season 2027 --dry-run`.
   Revisar fallos, exclusiones e identidad; respaldar antes de repetir sin `--dry-run`.
   La ingesta es idempotente, no entrena. No extrapolar PRE a temporada regular.
3. Fútbol: capturar el mes completo por liga con
   `.venv/bin/python -m scripts.auditar_fuente_espn_soccer --liga esp.1 --mes 202610 --salida /RUTA_EXTERNA/lote.json`.
   Repetir para `eng.1`, `ita.1`, `ger.1`, `fra.1`. Los 401/403 detienen la fuente;
   no cambiar identidad/red/proveedor para eludirlos. No limitar finales si se pretende ingesta completa.
4. Validar snapshots con `.venv/bin/python -m scripts.ingerir_espn_soccer_capturas --archivo /RUTA_EXTERNA/lote.json`;
   solo tras revisión aplicar con `--aplicar`. Después validar el vínculo con
   `.venv/bin/python -m scripts.sincronizar_espn_futbol --manifiesto /RUTA_EXTERNA/manifiesto.json --archivo /RUTA_EXTERNA/lote.json`.
   Cualquier identidad nueva exige acreditar/ampliar el manifiesto. Repetir con
   `--aplicar` solo tras backup y ensayo; no usar fuzzy matching ni fabricar campos por tiempo.
5. Consultar estado/calendario otra vez y comprobar reimportación 0 cambios.
   Entrenamiento NBA, si se necesita, es una operación independiente:
   `.venv/bin/python scripts/entrenar_modelo_nba_explicito.py --entrenar`.
   Requiere dataset apto y backup; reload/ingesta no son autorización automática para entrenar.

El manifiesto acreditado de esta entrega y los snapshots están en la carpeta
externa `PREPARACION_USO_INTEGRAL_2026-10-15`; no se incluyen datos masivos en Git.

## Fútbol: límites observados

Vínculo `2378058`, CI 38837743890 **4/4 verde**. Ensayo aislado con contrato/datos
reales, rollback DDL+DML y reimportación 0. Neon: 337 eventos nuevos, 200 finales,
136 programados, un abandonado→suspendido; dos clubes y cinco temporadas nuevas.
Las huellas del histórico de 23.919 partidos y de seis tablas de apuestas/predicciones
permanecen iguales. Los 200 finales FT no contienen desgloses 1T/2T; se conservan NULL.

La ruta `PredictorFutbol.cargar_modelos()` sin archivos inicializa modelos vacíos,
no restaura parámetros de BD. Además, el gestor legacy espera `tipo_modelo`, columna
que no existe en el contrato Neon actual (`mercado_principal` sí existe).
No se entrenó/publicó/activó un modelo ni calibrador fútbol. La cobertura nueva FT
no basta para los modelos de goles/corners por tiempos. Sigue pendiente reparar
persistencia/serving y validar datasets por target antes de entrenar, no solo registrar una versión.

## Cadena prospectiva NBA Q1

Migración `2026-10-15_cadena_prospectiva.sql`: dos tablas paralelas, sin modificar
predicciones/apuestas históricas. Triggers rechazan UPDATE/DELETE/TRUNCATE; una
corrección necesita evidencia separada y revisión, nunca sobrescritura automática.

**Aplicación acreditada:** `2b142e0`, CI
[38838845268](https://github.com/UNIVERSIDAD21/AnalyticsPredict/actions/runs/38838845268)
4/4 verde; ensayo con rollback, preflight y aplicación transaccional. Los doce
eventos NBA del scoreboard2026-10-16 (temporada2027/tipo1/preseason) quedaron
congelados desde2026-10-16T02:09Z para inicios2026-10-16T23:00Z a17T02:30Z.
Umbral técnicoQ1=55.5, sin selección por resultado/probabilidad. Reimportación0,
12hashes/cadenas temporales verificados independientemente, nueve huellas del
histórico intactas. EstadoHTTP200:12congeladas/0outcomes. No es evidencia de eficacia.

CLI: `.venv/bin/python scripts/seguimiento_prospectivo_nba.py --fecha 2026-10-16`.
Por defecto solo consulta/lista NBA ESPN. Una captura exige elegir un ID exacto:
añadir `--evento ID --linea 55.5 --congelar`. La línea es un **umbral técnico**
predeclarado, no una línea de mercado. No hay cuotas, selección de lado, picks,
stakes ni recomendaciones. El módulo NBA descriptivo sigue siendo independiente.

Se conserva evento original/hash, IDs/equipos/inicio UTC, features, coeficientes Q1,
hash de artefacto/dataset, modelo, fit_completed_at, distribución/media/desviación,
p_raw y ausencia explícita de calibrador/p_calibrada. El reloj de PostgreSQL exige
`fit_completed_at < congelado_en < inicio_utc`; el feed debe seguir sin iniciar.
La clave evento/mercado/umbral impide convertir reanálisis en muestras adicionales.

Después de un final: mismo CLI/día/ID con `--resolver UUID_PREDICCION`.
Exige mismo inicio/IDs, estado final, cuatro cuartos y suma/totales coherentes.
El outcome guarda fuente/evidencia y hora posterior; no puede sobrescribirse.
Reprogramaciones, revisiones o desacuerdo se detienen para revisión. ESPN por sí
solo **no es fuente independiente**, incluso al consultarlo dos veces.

La normal Q1 y la suma de varianzas son supuestos del Ridge existente sin
validación prospectiva. La disponibilidad histórica de outcomes de entrenamiento
no está acreditada. PRE y regular deben evaluarse por separado; múltiples umbrales
del mismo evento no son observaciones independientes. Conteos de captura/resolución
no certifican accuracy, calibración o rentabilidad. Se necesitan resultados futuros,
volumen por mercado, dependencia por evento e intervalos antes de promoción.

## Verificación

Suite sintética final: 751 passed, cero fallos/omitidas; 21 frontend tests,
lint/build verdes. Una regresión SQL adicional protege el contrato real de modelos
fútbol (no la columna legacy `tipo_modelo`). Seis GET API, seis rutas frontend y
detalle canónico de fútbol HTTP200. La presencia del SQL sola no implica aplicación;
en esta entrega sí se acreditó la aplicación/captura indicada arriba.

Navegación visual local pendiente por política del navegador registrada en la
etapa anterior; no se elude. Los GET y pruebas de componentes no sustituyen ese smoke.
NBA CDN oficial: ambos endpoints públicos de schedule consultados devolvieron
403; independencia interproveedor sigue bloqueada. No hubo reintentos con evasión.
