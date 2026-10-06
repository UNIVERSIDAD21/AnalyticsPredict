# Clasificación de datos deportivos dudosos — corte read-only 2026-10-06

**Estado:** categorías y exclusión preventiva de nuevas resoluciones NBA 0–0 implementadas; métricas históricas aún requieren filtro canónico. **No certifica** marcador ni resultado de proveedor.

## Hallazgos en Neon

| Grupo | n | Hecho observable | Clasificación operativa |
|---|---:|---|---|
| NBA sin `source` normalizado | 219 | Los 219 tienen `fuente_datos=ESPN`, `espn_game_id` y tipo REG; 138 muestran ambos totales positivos y 81 muestran 0–0. | `SOURCE_ALIAS_LEGACY`: procedencia parcial recuperable por ID ESPN, sin equiparar el alias faltante con verificación de resultado. |
| NBA 0–0 | 231 | 83 `source=SOFASCORE`, 81 `source=NULL` y 67 `source=ESPN` (58 REG, 9 POST); todos `valido=true` pero sin ganador ni puntos en cuartos. Intersección con grupo anterior: 81. | `ZERO_ZERO_NO_OUTCOME`: resultado no acreditado. Sin campo de estado original suficiente para distinguir programado, cancelado o error. |
| Predicciones NBA enlazadas a 0–0 | 66 | 42 pendientes; **24 ya resueltas** con outcome binario (12 COMPLETO, 8 Q1, 2 Q2, 2 Q3), fechas 2026-01-24/25. | Las 24 no son pares de resultado defendibles. No reescribir sin fuente primaria; excluir de métricas evaluables. |
| Apuestas NBA enlazadas a 0–0 | 5 | 4 GANADA y 1 PERDIDA, con ganancia registrada. | No atribuir P&L/ROI certificado a ese evento. Conservación y exclusión analítica pendientes de consolidar en KPI canónico. |
| Fútbol FINALIZADO sin goles completos | 25 | Los 25 tienen `fuente_datos=SOFASCORE`, ID de fuente, `datos_completos=false`; 3 registran corners/disparos. Fechas 2019-05-01 a 2023-11-18; cero predicciones enlazadas. | `FINALIZADO_SIN_GOLES`: no resolver 1X2 o mercados de goles; corners/disparos solo con completitud propia por mercado. No convertir NULL en 0. |

Los 219 y 231 **se superponen**; sumarlos como si fueran partidos distintos inflaría el problema. `valido=true`, `estado=FINALIZADO` o un ID de proveedor no demuestran por sí solos que haya marcador final íntegro. Ninguna fila fue actualizada, borrada o imputada.

## Regla de consumo y límites

El resolvedor NBA de predicciones y apuestas rechaza de ahora en adelante un partido cuyo **total local y visitante sean ambos cero**, incluso si los cuartos contienen cero. La comprobación aplica también con resolución forzada; no corrige retrospectivamente las 24 predicciones ni las 5 apuestas. El resolvedor fútbol ya deja `GOLES_*` sin valor real cuando faltan los goles requeridos; los 25 no tienen predicciones enlazadas hoy. La métrica por mercado de corners/disparos requiere campos propios, no el total de goles.

Las métricas históricas NBA publicadas antes de un filtro canónico de los 24 pares deben etiquetarse **descriptivas/no certificadas**. El gate H9/temporalidad ya mantiene toda la historia fuera de claims prospectivos. El siguiente trabajo de capa KPI debe excluir y contabilizar esos 24 pares (y 5 apuestas), incluyendo caches/precalculados; no basta cambiar un gráfico aislado.

## Checklist y criterio de aceptación

- [x] Clasificar 219 alias de fuente sin borrar identificadores.
- [x] Clasificar 231 marcadores 0–0 y el solapamiento de 81.
- [x] Clasificar 25 finalizados fútbol con goles nulos y mercados afectados.
- [x] Identificar 24 outcomes NBA y 5 apuestas ligados a 0–0.
- [x] Impedir nuevas resoluciones NBA basadas en 0–0.
- [x] Mantener Neon/histórico intactos.
- [ ] Confirmar estado final de los 231 eventos contra fuente primaria independiente; el campo local no lo demuestra.
- [ ] Excluir y contar los 24 pares y las 5 apuestas en **todos** los KPI/caches consumidores; pendiente capa canónica.
- [ ] Verificar resultados de los 25 partidos fútbol contra proveedor permitido o dejar formalmente sin outcome.

**Aceptación parcial:** clasificación técnica documentada y prevención futura; **no** hay certificación de resultados históricos ni cierre global del bloque E hasta propagar exclusiones a métricas. Siguiente acción: cotejo permitido de proveedores y filtro KPI central con pruebas SQL/API/UI.

## Adenda: exclusión en consumidores principales

La auditoría read-only mantiene 2.934 predicciones y 2.612 marcadas resueltas, pero aparta los **24 outcomes 0–0** antes de computar Brier/Log Loss/ECE: quedan 2.558 pares raw frente a 2.582 del corte original. La API de calibración y su curva enmascaran el outcome y el valor real de esas filas, exponen `n_excluidos_outcome_dudoso` y recalculan en memoria; el GET ya no usa un precálculo anterior ni ejecuta UPSERT. Esto **no** convierte el resto en evidencia prospectiva o independiente.

En bitácora, los cinco registros vinculados a 0–0 se conservan visibles. El gate de ROI combina calidad de fórmula/cuota y resultado acreditado: **107/181** binarias no evaluables (103 previas más 4 nuevas; la quinta ya se solapaba). El CLI de P&L clasifica por fila y deja solo **74 binarias** aritméticamente coherentes y sin 0–0, todavía **no certificadas**. Los otros endpoints agregados de salud/calidad/drift y eventuales caches históricos aún requieren revisión; el checklist de exclusión en **todos** los KPI sigue abierto.
