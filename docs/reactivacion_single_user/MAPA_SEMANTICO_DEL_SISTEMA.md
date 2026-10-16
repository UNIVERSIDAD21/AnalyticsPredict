# Mapa semántico vigente — AnalyticsPredict single-user

**Corte:** 2026-10-06. El mapa de `docs/borlty-deliverables/` es antecedente comercial, no contrato activo.

## Entidades y relaciones

- **Evento:** `partidos_baloncesto` mezcla NBA y Euroliga; toda consulta NBA filtra `competiciones_baloncesto.codigo='nba'`. `partidos_futbol` contiene estado y completitud separados para goles/corners/tiros. Un 0–0 sin acreditación no es outcome.
- **Predicción:** `predicciones_registradas` (NBA) y `predicciones_futbol` (fútbol), potencialmente muchas por evento/mercado. `modelo_version_id`, `calibrador_id` y timestamps deben tener procedencia; una probabilidad calibrada sin ID no se atribuye a calibración.
- **Apuesta:** `apuestas`, `apuestas_futbol` y combinadas son registros operativos separados de la predicción. `ganancia` histórica NBA es importe registrado, no profit auditado. Una apuesta sin `partido_id` no puede certificar resultado deportivo.
- **Fuente:** ESPN origina NBA; Euroliga tiene reconciliación oficial. Sofascore fútbol dio 403 y se etiqueta `SOURCE_UNAVAILABLE`; ESPN Soccer ya tiene337eventos/200FT capturados y vinculados al canónico (cierre15/10); eso no completa tiempos ni acredita independencia. Fuente de origen no equivale a verificación independiente.

## Estados de calidad que no se deben fusionar

1. `NO_DATA`: respuesta válida y completa sin eventos **para la ventana consultada**.
2. `SOURCE_UNAVAILABLE`: 403, error/JSON roto/contrato o lote incompleto; nunca interpretar como cero partidos.
3. `NO_EVALUABLE`: fila conservada pero excluida de una métrica por marcador, vínculo, fórmula o procedencia insuficiente.
4. `VALIDO_DESCRIPTIVO`: fórmula y outcome persistido compatibles para descripción, no para claim temporal ni prospectivo.
5. `NO_CERTIFICADO`: dictamen global actual para ROI, calibración, confidence y walk-forward.

**Granos y denominadores:** Win Rate registrado NBA usa 181 binarias, el diagnóstico aritmético/deportivo previo dejó114noevaluables; el gate de publicación16/10 excluye todas las resueltas sin soportes/unidad, incluidas las67soloaritméticas; `n` de Brier raw NBA es 2.558 pares descriptivos tras exclusiones de 0–0, no 2.558 juegos independientes. No sumar mercados del mismo partido como muestras independientes. ROI exige misma población en profit y stake, unidad conocida y ausencia de filas no evaluables. Sin denominador/evidencia, devolver `NULL` y UI `N/D`, nunca 0.

## Flujo prospectivo todavía abierto

`dataset/features congelados → fit_end/modelo/calibrador → predicción/odds antes de kickoff → outcome posterior independiente → KPI con n, ventana, exclusiones e incertidumbre`. Los 2.934 registros NBA históricos no completan esa cadena: 2.136 incompatibles, 476 ambiguos y 322 no determinables, cero válidos demostrados. El análisis interno NBA no ofrece picks, stakes ni recomendaciones.
