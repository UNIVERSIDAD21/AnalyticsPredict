# Predictor Euroliga — integración local, 21 de octubre de 2026

Orden del propietario: implementación de punta a punta en una pasada. Integración
funcional terminada; **no acredita igualdad de precisión con NBA ni certificación**.

## Uso y límites

Abrir `/euroliga` desde la navegación. Seleccionar fixture Euroliga o dos equipos,
periodo y línea. Informa Over/Under/push, media, desviación, intervalo nominal,
proyecciones Q1–Q4/total y ventaja local/visitante. Admite condicionamiento a los
marcadores de cuartos completos Q1–Q3, no reloj ni parcial del cuarto siguiente.

Todo se refiere a **40 minutos de regulación, sin prórroga**. Ventaja de puntos es
una aproximación continua, no moneyline con OT. Sin picks, stakes ni recomendaciones.
No hereda coeficientes, calibradores, cuotas, reglas contextuales ni sigma fijo de
ganador NBA. La línea introducida es manual, no una cotización verificada. Forma
reciente y H2H son contexto descriptivo; no modifican la distribución Ridge.

Una ejecución conserva un JSON nuevo en un journal Euroliga. Historial reabre la
salida original sin otro POST. No crea apuestas ni registros en tablas NBA. No
entrena al consultar, seleccionar temporadas, recargar o arrancar el servidor.

## Datos y modelo

- Snapshot inicial READ ONLY 22-oct02:36:58UTC: 2.741 filas/2.590 finales coherentes.
- Alta oficial E2026_61: Hapoel Tel-Aviv–Virtus Bologna,21oct,90–81. Cuartos local
  23/13/28/26, visitante25/23/14/19. Identidad exacta, snapshot/ausencia respaldados,
  ensayo revertido, idempotencia y postflight. Solo una alta, sin tocar otros partidos.
- Snapshot posterior: **2.742 filas/2.591 finales**, 61 de 2026–27; rango2018-10-11–
  2026-10-21,29 entidades históricas y69 fixtures próximos reconocibles.
- Refit servido: **euro-f9cc361e255b91196acc**, datasetSHA256
  `e33469fb44353afc801b1e409fc56432026ca616d369124a68ce7849d88cdfc3`.
- JSON versionado y publicación atómica en
  `~/.local/share/analyticspredict/euroliga/activo.json`, con copias en `versiones/`.
  Validación de dominio/formato/hash, índices, matrices finitas y covarianza positiva;
  sin pickle. Versionado propio por contenido, no FK de `modelo_versiones` NBA.
- Archivo NBA2123 con el mismo SHA256 inicial. Durante la tarea hubo altas
  concurrentes NBA en tres tablas. El preflight detuvo la escritura antes del DML;
  se tomó baseline fresca y se preservaron esos registros. Las huellas de todas las
  filas fuera del alta Euro fueron iguales durante ensayo/aplicación/postflight.
  No afirmar que toda la base permaneció estática durante la sesión.
- Contraste del feed oficial E2026: 61/61 finales de la temporada enlazados por
  source_game_id y FT exactos; no acredita completitud histórica mundial.
  Reconstrucción offline reprodujo ambos bloques de coeficientes y la salida UI
  exacta del artefacto final, sin otro POST ni publicación/reentrenamiento NBA.

## Método y evaluación medida

Mismas funciones `construir_matriz_diseno`/`ajustar_ridge`, alpha5 fijado, no pesos
NBA. Identidad equipo/rival/localía, dos orientaciones por juego y cuatro targets
por lado. Mínimo6 finales por equipo; fuera del soporte se abstiene. Menos de20
históricos o10 en la temporada reciente genera aviso. Besiktas solo tiene6.

TRAIN anterior a2024-09-01: **1.798** partidos. CAL hasta2025-09-01:330,292 utilizables
por identidad/muestra. CAL estima segundo momento de errores fuera de muestra en
8 targets, shrinkage diagonal0,1: **no ajusta calibrador probabilístico ni media**.
EVAL desde2025-09-01: **327/463**,136 abstenciones,cobertura70,63%.

| Periodo | MAE Ridge | MAE media liga TRAIN | Brier RAW de referencia |
|---|---:|---:|---:|
| Q1 | 6,3754 | 6,2583 | 0,2504 |
| Q2 | 6,0418 | 6,0812 | 0,2527 |
| Q3 | 5,9431 | 5,9646 | 0,2465 |
| Q4 | 6,0493 | 6,0322 | 0,2424 |
| Total regulación | 15,9832 | 15,6727 | 0,2579 |

El total no supera a una media de liga. Brier usa líneas de referencia derivadas
solo de TRAIN, no cuotas históricas;0,25 es probabilidad constante50%. Cobertura del
intervalo nominal80% del total:71,87%, **no calibrado**. No se cambió alpha/corte
para ocultar el resultado. Esto evalúa un candidato TRAIN antiguo, no el refit
final con2.591 partidos. La covarianza CAL se transfiere al refit como aproximación
explícita pendiente de validación propia. Separar fechas de juego no certifica
la disponibilidad histórica. Ninguna métrica retrospectiva equivale a eficacia futura.

Normal discretizada: conserva push en líneas enteras, cero en no enteras y
Over+Under+push=1. Condicionamiento gaussiano de la distribución conjunta para
cuartos completos; sin constantes NBA. No incorpora lesiones/plantillas actuales.

## Contratos y operación

| Operación | Efecto |
|---|---|
| GET `/api/euroliga/estado` | Artefacto y evaluación, sin entrenar |
| GET `/api/euroliga/equipos` | Catálogo propio, muestra/elegibilidad |
| GET `/api/euroliga/partidos` | Solo Euroliga; próximos30d por defecto,READ ONLY |
| POST `/api/euroliga/analizar` | Valida fixture/localía/temporalidad; calcula y conserva JSON local |
| GET `/api/euroliga/historial` | Lee capturas; no recalcula/escribe |
| GET `/api/partidos/proximos?competicion=nba` | Selector NBA aislado; calendario genérico compatible |

PostgreSQL Euroliga siempre READ ONLY, incluso POST/CLI. GET/HEAD reutiliza la
transacción protegida por `PoolAplicacion` sin reasignar `read_only` en transacción
activa. Regresión SQL real. Rechaza temporadas/cuotas NBA, equipos desconocidos,
fixtures ajenos/finalizados/pasados y datos live no soportados.

`backend/scripts/gestionar_predictor_euroliga.py --help`: exportarREADONLY,
entrenar offline, publicar, congelar y evaluar. Requiere snapshot/exportación
explícitos; `--entrenar --corte --salida`, más `--publicar` para activar. Salidas
nuevas, no sobrescribibles. No se publican datasets/modelos/capturas en Git.

Variables opcionales: `ANALYTICSPREDICT_MODELO_EUROLIGA_ACTIVO` y
`ANALYTICSPREDICT_EUROLIGA_JOURNAL`. Restauración operativa: copiar atómicamente una
versión JSON previa validada sobre activo; no reentrenar para recargar. Eliminar
una entrada de navegación no borra evidencia ni resultados deportivos.

## Cohorte futura

Congeladas **69 distribuciones,0 abstenciones**, con modelo,identidad,fecha,hashes
 y manifiesto inmutable;63 anteriores a la fecha del evento. Los6 del22oct no
acreditan anterioridad porque ya era22octUTC y el catálogo no guarda kickoff.
No inferir hora. La línea170,5 de la cohorte es referencia fija, no cotización.
Estado inicial **0outcomes/MAEN/D** y fuente independiente no acreditada.
Evaluar después solo une IDs/localía/fecha originales con finales válidos, verifica
hashes y orden fit<freeze<fecha; no regenera ni reentrena. Sin cron/acciones futuras.

## Verificación y evidencia

**994 backend/0 fallos/0 skips**,2deprecaciones conocidas,PGsintético propio55439.
**42 frontend**,lint/build aprobados.6GETreales200. UnPOSTvisualreal, sin repetición
para capturas. Desktop/móvil390px verificados, sin overflow. Historial reabre salida
original. Pruebas cubren live,aislamientoNBA,push,abstención y rechazo de identidad.

Incidencias preservadas: arnés inicialSQL_ASCII falló antes depytest; clúster propio
UTF8 posterior correcto. Residuo flotante de push corregido. GET real detectó doble
configuraciónREADONLY; corregida y cubierta. Capturas auténticas/datasets/modelos/
cohorte/logs/acta/commit/CI en entrega externa `PREDICTOR_EUROLIGA_INTEGRAL_2026-10-21/`.
El acta contieneSHA,CI y procesos finales. **NO CERTIFICADO**: calibración,
evaluación prospectiva e igualdad de eficacia frente a NBA continúan pendientes.
