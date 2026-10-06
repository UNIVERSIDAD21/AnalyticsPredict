# Reconciliación P&L NBA — clasificación sin reescritura

**Corte:** 2026-10-06, Neon solo lectura. **Estado:** histórico clasificado; P&L/ROI globales **NO CERTIFICADOS**. Evidencia por fila en entrega privada `RECONCILIACION_PNL_NBA_2026-10-06`, fuera de Git.

## Fórmula y clasificación

- Cuota decimal y `stake > 0`. Victoria: `stake × (cuota − 1)`; derrota: `−stake`; anulada/push: `0`. Tolerancia absoluta: `0,02` en la unidad registrada.
- Se verifica además que `cuota` no discrepe más de `0,02` de `cuota_over`/`cuota_under` cuando la cuota del lado está disponible.
- `ARITMETICAMENTE_CONSISTENTE` solo verifica esos campos persistidos; **no** prueba apuesta real, unidad monetaria, fuente de cuota, outcome independiente ni ausencia de leakage. `NO_EVALUABLE` nunca se corrige por inferir otro stake.

| Grupo | n | Dictamen |
|---|---:|---|
| Binarias (`GANADA`/`PERDIDA`) | 181 | Universo auditado |
| Incompatibles con fórmula | 102 | No evaluables |
| Adicional con importe conciliable, pero cuota contradice la del lado | 1 | No evaluable |
| Binarias con aritmética y cuota de lado conciliables | 78 | Solo subconjunto descriptivo, no certificado |
| Anulada con ganancia 0 | 1 | Fuera del denominador binario |

Las 102 diferencias no tienen una única convención demostrable. **30** son numéricamente la mitad de la fórmula, pero otras siguen factores distintos. La hipótesis de stake real diferente no se convierte en corrección: `stake_porcentaje`, `bankroll_momento` y `notas` están vacíos en las 182 filas, y no existe columna de moneda/unidad ni procedencia de cuota o versión del modelo en `apuestas`. Cinco filas presentan discrepancia entre `cuota` y la cuota del lado; una de esas cinco habría pasado el control solo aritmético. Faltan `partido_id` en 40/182.

## Métricas después de clasificar

El archivo privado computa `n`, Profit neto de fórmula, ROI aritmético **no certificado**, Win Rate registrado, stake promedio y ventana (`2026-01-10` a `2026-04-03`) solo sobre las **mismas 78 filas** binarias compatibles; también desglosa mercado, Q1–Q4 y rangos de cuota. No se comunica ese ROI como rendimiento del histórico completo: el subconjunto excluye 103/181 casos, la unidad del stake es desconocida y faltan fuentes/outcomes independientes. Los segmentos Q2 (n=1) y cuota >2 (n=1) son insuficientes para inferencias.

## Contrato de producto

- `GET /api/bitacora/resumen` conserva `ganancia_total` como **importe registrado**, añade `n_pnl_no_evaluable_nba` y devuelve `roi: null` para cualquier segmento que contenga P&L NBA no evaluable.
- `GET /api/bitacora/metricas` añade `n_pnl_no_evaluable` global/mercado/confianza/mes y devuelve `roi: null` en esos cortes. Win Rate permanece rotulado como resultado registrado, no como acierto prospectivo.
- Dashboard, Bitácora y Métricas muestran N/D y el conteo excluido. Ningún valor histórico de `apuestas` se sobrescribió.
- El GET de bitácora ya no escribe telemetría a archivo al construir el contrato; el endpoint de uso conserva lectura de su histórico, sin incrementarlo.

## Reproducción y límites

El CLI `backend/scripts/auditar_pnl_nba.py` abre una transacción **READ ONLY** y opcionalmente escribe un JSON privado por fila con modo 0600. El test SQL de la misma regla de API usa PostgreSQL sintético. El JSON de evidencia no contiene credenciales ni equipos, pero contiene IDs/importes personales y permanece fuera del repositorio.

**Pendientes para certificación:** obtener prueba primaria de stake/unidad, cuota/fuente/timestamp y resultado; resolver las 103 filas sin inventar datos o excluirlas de forma definitiva; cotejar temporalidad y outcomes; acumular nueva cadena prospectiva. Hasta entonces el ROI global es `N/D` y no existe afirmación de rentabilidad futura.

**Adenda por resultados 0–0:** el corte aritmético anterior se conserva como antecedente. Tras cruzar con `partidos_baloncesto` sin modificar Neon, cinco apuestas resueltas enlazan a marcador 0–0: cuatro habían pasado el control aritmético y una ya era no evaluable. El gate combinado deja **107/181 binarias no evaluables** y **74** solo aritméticamente coherentes, sin certificación de outcome ni cuota primaria. El CLI y los GET de bitácora ya incorporan esta exclusión en ROI; los importes originales siguen visibles como registrados.
