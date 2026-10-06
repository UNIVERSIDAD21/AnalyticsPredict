# Calibración fútbol — procedencia, no certificación

**Estado:** flujo corregido en código; aplicación prospectiva real y eficacia **NO CERTIFICADAS**.

## Evidencia observada

- Consulta de solo lectura en Neon: 24 mercados con un artefacto Platt activo por mercado, entrenados el 2026-01-31. El gestor reconstruyó 24/24 con su UUID; los 24 transformaron una entrada de prueba `p=0,2` a un valor distinto. Esto demuestra carga/ejecución del artefacto, no calidad fuera de muestra ni uso histórico.
- Las 567/567 predicciones fútbol persistidas tienen `prob_over_calibrada == prob_over` y `calibrador_id IS NULL`. De 81 pares raw/outcome, hay **0 pares calibrados con procedencia**. No se reescribieron esos registros.
- El esquema vigente guarda raw en `prob_over`; no existe `prob_over_raw` en esa tabla. El reporte y el endpoint de métricas usan esa columna real y no hacen `COALESCE` de raw para simular calibración.

## Corrección verificable

- El gestor devuelve `(p_calibrada, calibrador_id)` únicamente tras cargar y aplicar un artefacto identificado con salida finita en `[0,1]`; sin ello devuelve `(null, null)`. Una transformación identidad **sí** puede ser calibración si realmente se ejecutó con ID; la igualdad numérica sola no prueba ni refuta aplicación.
- La conversión ML al API, la persistencia y la UI separan raw de calibrada. La ruta heurística sin artefacto identificado y la mezcla ML/heurística no se etiquetan como calibradas. El ajuste por tamaño de muestra tampoco se presenta como salida del calibrador.
- El endpoint `/api/futbol/metricas/calibracion` informa `n_raw`, `n_calibradas`, Brier raw y métricas calibradas `null` cuando no hay pares con ID. La mejora se calcula solo sobre pares coincidentes.
- Pruebas dirigidas cubren cambio `0,2 → 0,5`, ausencia/identidad/salida inválida, persistencia de raw/null/UUID, y representación raw/calibrada del frontend.

## Checklist de aceptación

- [x] Localizar artefactos activos, mercados cubiertos y versión/fecha de entrenamiento observables.
- [x] Explicar el 567/567 histórico: el campo duplicó raw sin `calibrador_id`; no hay prueba de transformación aplicada en esas filas.
- [x] Impedir que inferencia nueva, persistencia, métricas o UI llamen calibrada a una salida sin artefacto identificado en las rutas corregidas.
- [x] Probar transformación distinta, ausencia e identidad con procedencia.
- [ ] Observar predicciones nuevas de un partido elegible con versión del modelo y artefacto trazados, y verificar read-only lo persistido y el corte temporal.
- [ ] Medir calibración por mercado con outcomes posteriores y masa resolutiva suficiente; los 81 pares históricos solo son raw.

**Siguiente acción:** validar el flujo prospectivo en una ejecución controlada cuando haya modelo/partido apto, sin promover mercado ni certificar rentabilidad por la existencia de artefactos.
