# Validación temporal por dominio · candidatos, no certificación

Protocolo V1 congelado antes de medir, snapshot SHA-256 `4ee43bc6275c3a30509f1f9a793db26ba039d6c2b4e3518b60c7a0edb7dc9ad3`. Datos ya observados: TEST retrospectivo, no prospectivo ni inédito. No se publican pesos o calibradores activos.

Ejecutables reproducibles: `backend/scripts/evaluar_agendas_temporal.py` y `evaluar_cohortes_futbol_cal.py`. Entradas/cohortes/parámetros/curvas/intervalos completos fuera del producto, sin reemplazar evidencias previas.

NBA/Euroliga: TRAIN<2024-07-01; CAL dispersión hasta2025-01-01, CAL calibrador hasta2025-07-01; TEST posterior hasta26-oct2026. WNBA: TRAIN<2024-01-01; CAL dispersión hasta15-jul2024, calibrador hasta2025-01-01; TEST posterior. Sin dividir fechas simultáneas. Ridge y muestras por dominio; líneas fijadas sólo en TRAIN. Baseline de medias TRAIN y dispersión CAL anterior. Temperatura multiclase única ajustada sólo en CAL, conservando masa push y suma uno; se abstiene si CAL<200, menos20 casos por lado o menos10 pushes para línea entera.

| Candidato de regulación PRE | TRAIN | CAL dispersión | CAL calibrador total | TEST elegible / predicho | MAE total | Brier RAW / referencia | log loss RAW |
|---|---:|---:|---:|---:|---:|---:|---:|
| NBA |7059|481|750|1274 /1274|16.5273|0.51850 /0.49930|0.71342|
| Euroliga |1798|144|169 (148 soportados)|450 /315|16.2696|0.51989 /0.49582|0.71417|
| WNBA |984|142|98|616 /450|15.1198|0.48372 /0.49152|0.67588|

Brier es **suma multiclase**, no el Brier binario de informes anteriores. Cada fila corresponde a la línea total derivada de TRAIN; no son métricas universales de todas las líneas. Se guardan además Q1–Q4, cierres Q1–Q3 para candidatos Euroliga/WNBA, líneas enteras con push, curvas10bins, intervalo80RAW, abstenciones y bootstrap pareado por día200réplicas/seed20261026.

NBA ajusta temperatura en CAL: Brier TEST0.50719, mejora sobre RAW pero no supera la referencia0.49930. Euroliga/WNBA no tienen CAL suficiente para calibrador; sus coberturas son70% y73.05%. Ninguno tiene la evidencia prospectiva independiente requerida (0/200). Los gates también exigen TEST>=300, cobertura>=90%, mejora Brier>=0.002/logloss>=0.005, no inferioridad frente a referencia e IC95% de diferencia Brier bajo0. **Ningún calibrador/modelo promovido. RAW/N/D se mantiene.**

Estos candidatos no son el refit activo: NBA usa dispersión CAL de desarrollo, no la dispersión in-sample del reconstruido; WNBA Gaussian de regulación no equivale al serving Sobol/OTv2. No transferir estas métricas a ganador, total con OT WNBA, cortes NBA, ajustes heurísticos de contexto o selecciones históricas de temporadas. Esos ámbitos continúan sin certificación por esta cohorte. Las evaluaciones v1/v2 originales WNBA y sus artefactos siguen intactos.

## Fútbol

Se reutilizaron los ocho archivos de cohortes causales Américas previamente archivados (3.686 encuentros de sus cohortes originales), verificando hashes antes/después. Primera mitad de instantes como CAL, segunda como TEST; estimador real histórico y referencia previa730d/min40 conservados, sin regenerar probabilidades ni fingir un TEST no observado. Cinco familias con campos evaluables por competición cuando hay muestra; córners por mitades sin fuente permanecen N/D y MLS is Back sin pares de referencia suficientes no admite calibrador. Se guardan Brier/log loss/MAE, curvas, bootstrap, temperatura y tamaños concretos; ningún cambio activo.

Las otras doce competiciones de fútbol no heredan estas métricas. No existe en este protocolo una cohorte congelada y conciliada suficiente por sus mercados/modos; además las identidades de ciertas copas legacy siguen pendientes de auditoría. La presencia de resultados en BD no acredita emisión predictiva prospectiva. Para esos dominios, la calibración y superioridad son N/D, no cero ni una mejora demostrada.

Consultar, sincronizar o ingerir resultados no entrena, activa ni certifica modelos. Ni CI, una buena MAE ni una temperatura retrospectiva prometen precisión futura o rentabilidad.
