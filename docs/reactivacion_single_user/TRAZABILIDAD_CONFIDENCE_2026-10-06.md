# Trazabilidad de `confidence` — corte 2026-10-06

**Estado: fórmula trazada; validación predictiva pendiente.** No se alteran thresholds ni sizing en este corte. `confidence` es una etiqueta heurística, no una probabilidad calibrada ni garantía de ROI.

## NBA — ruta principal

1. `backend/motor/nba_predictor_cuartos.py::determinar_confianza` suma tres puntajes (0–2 cada uno): desviación total `<5,5` = 2, `<7,5` = 1, resto = 0; probabilidad `>=0,70` = 2, `>=0,60` = 1, resto = 0; distancia normalizada `|media−línea|/max(desviación,1e-9)` `>=1,5` = 2, `>=1,0` = 1, resto = 0. Total posible 0–6. **La tercera variable se llama `puntaje_edge` en código pero no es edge de cuota.**
2. `backend/motor/tipos.py::FactoresConfianza.obtener_nivel`: total `>=3` = ALTA, `>=2` = MEDIA, resto = BAJA. No hay normalización estadística ni estimación de incertidumbre de esa etiqueta. `tamano_muestra="moderado"` y `frescura_datos="aceptable"` están fijos en el constructor, no se calculan desde el dataset.
3. `backend/motor/ajustes/motor_ajustes.py` puede modificar la etiqueta contextual: +0,2 por H2H con al menos 5; −0,5 por back-to-back; −0,3 por diferencia de descanso >=3 días; −0,2 por H2H distante >8; −0,3 por ajuste de media >6. Mapea ALTA/MEDIA/BAJA a 2/1/0, limita a [0,2] y vuelve a clasificar con cortes 1,5/0,75. Esto no cambia la probabilidad raw por sí mismo y no debe confundirse con calibración.
4. `backend/api/rutas_analisis.py` expone nivel/factores en la respuesta; el frontend (`PaginaPrincipal`, `ResultadoAnalisis`, `FormularioGuardarApuesta`) presenta la etiqueta y puede enviarla como `confianza_sistema` al guardar. `backend/api/rutas_bitacora.py` persiste y segmenta por esa etiqueta. Las predicciones registradas guardan probabilidades/versiones por otra ruta; la apuesta histórica no prueba por sí sola que su confidence provenga de un modelo congelado.

## Fútbol — semántica distinta

`backend/servicios/b3_estabilizacion_futbol.py::nivel_confianza_b3` usa tamaño total, tamaño relevante y probabilidad extrema (`p>=0,75` o `p<=0,25`): ALTA si `n_total>=80` y `n_relevante>=25` y extrema; MEDIA si `n_total>=40` y `n_relevante>=12`, o extrema con `n_relevante>=8`; BAJA en otro caso. `rutas_analisis_futbol.py` eleva ALTA a MUY_ALTA con `p>=0,88` o `p<=0,12`, y puede degradar por muestra insuficiente. El predictor ML alternativo usa cortes de 5/3 partidos por equipo; no mezclarlo con la etiqueta B3 sin registrar `fuente` y versión.

## Deuda para validar, no para rediseñar aún

- En la bitácora NBA hay 94 ALTA, 53 MEDIA y 34 BAJA entre resultados binarios; son segmentos descriptivos y el P&L de 102/181 filas no concilia. No inferir que ALTA sea mejor.
- La validación requiere outcome contrastado, probabilidad raw/calibrada, mercado/cuarto, cuota capturada al momento, modelo/calibrador, timestamp y P&L reconciliado. Comparar Brier/Log Loss/ECE y win rate por cohorte temporal con intervalos, sin tratar predicciones del mismo partido como independientes.
- Mantener thresholds actuales como heurística hasta obtener muestra prospectiva válida. No usar la etiqueta como sustituto de calibración, edge o política de stake.
