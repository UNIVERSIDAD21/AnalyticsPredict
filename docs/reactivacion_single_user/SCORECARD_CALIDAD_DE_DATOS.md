# Scorecard de calidad — corte read-only 2026-10-06

**Estado: NO CERTIFICADO.** Corte de Neon `2026-10-06T15:37:17Z`, generado con `backend/scripts/auditar_corte_analitico.py` y evaluado con `backend/scripts/scorecard_calidad_single_user.py`. No hubo ingesta, entrenamiento, backfill ni escritura en BD durante el corte. Este archivo registra agregados; no contiene filas ni IDs personales.

| Control | Valor observado | Dictamen |
|---|---:|---|
| NBA partidos / últimos 30 días | 12.767 / 0 | OBSERVAR; último 2026-05-05, revisar calendario y feed |
| Fútbol partidos / finalizados / finalizados últimos 30 días | 23.919 / 23.637 / 0 | OBSERVAR; último finalizado 2026-03-22 |
| Duplicados por ID de fuente NBA / fútbol | 0 / 0 | OK solo en IDs no nulos |
| NBA sin `source` / 0–0 por clasificar | 219 (1,7154 %) / 231 | OBSERVAR; no borrar ni imputar |
| Fútbol corners/disparos completos entre finalizados | 18.300 (77,421 %) / 18.896 (79,943 %) | OBSERVAR; bajo 95 % inicial por mercado |
| P&L NBA no evaluable | 102 incompatibles con fórmula (79 GANADA + 23 PERDIDA) y 1 adicional con cuota del lado discrepante, de 181 resultados binarios | CRITICO; ROI/profit globales N/D/no certificados |
| Cutoff NBA posterior al día de generación | 2.136 de 2.934 predicciones | CRITICO; no afirmar no-leakage |
| Predicciones fútbol sin versión modelo/calibrador | 567 / 567 de 567 | CRITICO/OBSERVAR; no atribuir calibración |
| Probabilidades fuera [0,1] NBA/fútbol | 0 / 0 | OK en columnas auditadas |
| Stake/cuota inválidos en NBA resuelta | 0 | OK; no resuelve P&L inconsistente |
| Fútbol finalizados sin goles / predicciones huérfanas | 25 / 0 | CRITICO para resolución de esos 25 |
| Marcadores extremos NBA / fútbol (umbrales de revisión) | 0 / 0 | OK; no prueba ausencia de otros outliers |

**Disponibilidad de fuente, prueba read-only independiente del corte:** ESPN Scoreboard `20261005`: HTTP 200, JSON con 5 eventos. Sofascore `unique-tournament/8`: HTTP 403 tanto con `requests` como con `curl_cffi` impersonando Chrome. No se guardaron registros por esos probes. La fuente ESPN responde, pero el dry-run de ingesta 2026-10-01 a 2026-10-06 con `--season 2027` se detuvo antes de consultar partidos porque no existe temporada NBA 2026–27 en el catálogo de Neon. No confundir disponibilidad HTTP con pipeline completo.

**Cobertura de pruebas:** `backend/tests/calidad/test_reglas_single_user.py` verifica que P&L/cutoff críticos bloquean certificación, cero observaciones no se interpreta como caída de fuente, 95 % de cobertura es frontera válida y `NULL` queda NO_EVALUABLE. La suite global segura se registra aparte; este scorecard no la reemplaza.

El dictamen solo cambia tras reconciliar histórico, corregir procedencia temporal y verificar feeds/outcomes independientes. Fútbol continúa beta. El módulo NBA interno continúa sin picks, stakes ni recomendaciones.

## Corte posterior a ingesta NBA controlada

A las `2026-10-06T15:47:56Z` se repitió la auditoría read-only tras insertar 8 partidos de pretemporada ESPN (ver `INGESTA_NBA_CONTROLADA_2026-10-06.md`). NBA: **12.775 partidos**, último 2026-10-06, **8** en últimos 30 días; `NBA-FRESH-30` pasa a `OK` como observación de BD. Duplicados por ID de fuente 0, sin source 219 y 0–0 231 sin cambio. El scorecard sigue **NO_CERTIFICADO** con 10 alertas locales. La tabla anterior es el corte previo, no el estado posterior.

Al integrar el probe HTTP read-only separado, ESPN `200`/JSON válido figura `OK` y Sofascore `403` figura `CRITICO` por fuente bloqueada. El scorecard combinado tiene **11 alertas locales** y sigue NO_CERTIFICADO. Sin probe, ambas reglas permanecen `NO_EVALUABLE`; no se imputan estados desde la fecha del último partido.
