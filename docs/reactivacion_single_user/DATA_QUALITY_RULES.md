# Reglas de calidad de datos — single-user (2026-10-06)

Esta es la versión operativa para la reactivación. Los documentos homónimos de `docs/borlty-deliverables/` son antecedentes comerciales; sus alertas por Telegram/email y sus afirmaciones de madurez no gobiernan este corte. La base se lee con `backend/scripts/auditar_corte_analitico.py`, que exige transacción read-only. El evaluador puro es `backend/calidad/reglas_single_user.py`.

## Semántica

- `OK`: la regla calculable cumple el umbral. No certifica el modelo ni el deporte.
- `OBSERVAR`: deuda o posible anomalía; conservar filas y clasificar antes de excluir.
- `CRITICO`: impide usar la métrica o trazabilidad afectada como certificada.
- `NO_EVALUABLE`: falta dato/medición; nunca convertir en cero o `OK`.
- Las reglas de los últimos 30 días son señales de **observaciones en BD**, no prueba de caída de ESPN/Sofascore. Comparar con calendario/temporada y comprobar fuente por separado.

## Reglas ejecutables y umbrales iniciales

| Regla | Grano y denominador | Umbral | Acción ante falla |
|---|---|---|---|
| `NBA-FRESH-30`, `FUTBOL-FRESH-30` | partidos NBA / finalizados fútbol en BD durante 30 días | ≥1 observación; contextualizar con calendario | OBSERVAR; verificar feed y temporada, no declarar outage automáticamente |
| `NBA-DUP-ID`, `FUTBOL-DUP-ID` | IDs de fuente no nulos | 0 duplicados | CRITICO; bloquear ingesta hasta resolver clave; no deduplicar filas sin ID por esta regla |
| `NBA-SOURCE-NULL` | partidos NBA sin `source` / todos los partidos NBA | ≤1 % histórico | OBSERVAR; preservar procedencia desconocida |
| `NBA-SCORE-00` | partidos NBA con total 0–0 | 0 **sin clasificar** | OBSERVAR; diferenciar programado/cancelado/error antes de modelar |
| `FUT-CORNERS-COVERAGE`, `FUT-DISPAROS-COVERAGE` | finalizados con datos completos / todos los finalizados fútbol | ≥95 % para usar mercados respectivos | OBSERVAR y mantener beta; no completar ceros artificiales |
| `NBA-PNL-CONSISTENCY` | apuestas GANADA/PERDIDA con stake/cuota y ganancia | 0 incompatibles; error absoluto ≤0,02 por fila | CRITICO para ROI/profit; no reescribir histórico a ciegas |
| `NBA-FIT-END` | predicciones con cutoff posterior al día de generación | 0 | CRITICO para afirmación no-leakage; mismo día también exige hora |
| `FUT-TRACE-MODEL`, `FUT-TRACE-CAL` | predicciones sin versión/calibrador ID | 0 para evidencia por versión/calibrador | CRITICO/OBSERVAR; no llamar «calibrada» a una probabilidad sin procedencia |
| `NBA-PROB-RANGE`, `FUT-PROB-RANGE` | predicciones con probabilidad fuera de [0,1] | 0 | CRITICO; rechazar cálculo de Brier/Log Loss sobre fila inválida |
| `NBA-STAKE-ODDS` | apuestas GANADA/PERDIDA con stake ≤0 o cuota ≤1/nulos | 0 | CRITICO para retorno monetario |
| `FUT-ORPHAN-GAME`, `FUT-GOALS-NULL` | predicción sin partido / finalizado sin goles | 0 | CRITICO para trazabilidad/resolución del mercado |
| `NBA-SCORE-OUTLIER`, `FUT-GOALS-OUTLIER` | marcador <0 o NBA equipo >250 / fútbol equipo >30 | 0 para revisión | OBSERVAR; umbral de revisión, no eliminación automática |
| `ESPN-AVAILABILITY`, `SOFASCORE-AVAILABILITY` | HTTP + JSON válido en endpoint documentado | respuesta utilizable y contrato parseable | NO_EVALUABLE hasta probe externo; 403 es fuente bloqueada, no calendario vacío |

La integridad FK materializada no sustituye la prueba de orden temporal `fit_end < prediction_time < outcome_time`. Para pares de calibración se exige `p∈[0,1]`, outcome binario resuelto, ID de modelo/calibrador aplicables, corte anterior y `n` por mercado/version. Un valor `NULL` significa no medido, no error cero.

## Ejecución y límites

```bash
cd backend
python scripts/auditar_corte_analitico.py > /tmp/corte_single_user.json
python scripts/probar_fuentes_single_user.py > /tmp/fuentes_single_user.json
python scripts/scorecard_calidad_single_user.py /tmp/corte_single_user.json --fuentes /tmp/fuentes_single_user.json > /tmp/scorecard_single_user.json
python -m pytest -q tests/calidad/test_reglas_single_user.py
```

El primer comando necesita acceso protegido de solo lectura a Neon y nunca imprime la URL. El segundo solo consulta HTTP externo, no ingiere datos; si se omite, disponibilidad es `NO_EVALUABLE`. Las alertas se quedan en JSON local. Estos umbrales son guards iniciales; antes de promover un mercado se exige masa resolutiva, walk-forward y scorecard por mercado con evidencia temporal. No hay notificaciones externas por decisión del propietario.
