# Modos NBA y resultados comunes de Baloncesto — 2026-10-22

## Uso

En **Baloncesto**, elegir NBA o Euroliga y configurar equipo/partido, mercado,
línea y **Modo de análisis**: prepartido o corte al cierre de Q1, Q2 o Q3.
Introducir los puntos de cada cuarto terminado, **no acumulados**. No se admite
reloj, parcial del cuarto siguiente ni Q4. Los mercados ya observados se deshabilitan
y se rechazan también en la API. Cambiar parámetros invalida el resultado previo.

NBA prepartido sigue usando `/api/analizar`. Los cortes NBA usan exclusivamente
`/api/analizar-en-vivo`, conservando identidad/localía/fecha y los marcadores
suministrados. Un corte incompleto nunca se deriva silenciosamente a prepartido.
En modo al cierre se utiliza el modelo cargado, sin selección de temporadas,
reentrenamiento, cuotas, calibradores prepartido, picks, sizing o guardado de apuestas.
**Es solo consulta**: no se inserta en apuestas, bitácora financiera ni predicciones
prepartido. La respuesta identifica modo, cuartos, método y versión del modelo.
Euroliga conserva su journal propio; reabrir capturas no repite POST.

## Método NBA al cierre y límites analíticos

Se conserva el ajuste heurístico de ritmo existente: residuos de los cuartos
observados frente a sus medias base, ponderaciones Q1/Q2/Q3 0,15/0,35/0,50
renormalizadas sobre los cuartos disponibles y peso de traslado 0,5 por defecto.
No se optimizaron pesos ni se entrenó un candidato nuevo.

- Las medias de los cuartos observados son sus puntos reales; dispersión cero.
- Solo se ajustan medias de cuartos pendientes, con límite físico inferior cero.
- La dispersión del total se calcula con las varianzas de los cuartos pendientes,
  suponiendo independencia; **no es una covarianza condicional estimada**.
- El ganador aproximado en regulación usa esa dispersión pendiente; no hereda el
  sigma fijo de 12,5 del cálculo prepartido de ganador NBA completo.
- No se aplican a un corte calibradores, cuotas o reglas de ajuste contextual de
  prepartido. Forma y H2H se mantienen descriptivos.
- La salida se etiqueta por cierre, no como pronóstico live actualizado. Son
  **48 minutos de regulación sin OT**, probabilidades RAW y eficacia no certificada.

Esto corrige la aritmética de lo observado y separa modos; **no demuestra mejor
rendimiento predictivo, calibración ni validez prospectiva**. Los intervalos o
porcentajes aún dependen de supuestos aproximados. Los parciales son entrada manual,
no un marcador oficial obtenido automáticamente. No se resuelve ni regenera ninguna
cohorte prospectiva existente.

API: exige Q1→Q2→Q3 completos/consecutivos, puntos enteros0–100 por lado, mercado
posterior al corte o COMPLETO y sin cuotas/temporadas PRE. Rechaza campos extra como
reloj o marcador_q4. El modelo también valida cortes cuando se invoca directamente.

## Un único resultado, no otra pantalla Euro

`ResultadoEuroliga` solo adapta datos y delega al **mismo `ResultadoAnalisis`**
que usa NBA. Comparten panel de advertencias, estado, encabezado del encuentro,
selección del usuario, tarjeta de ganador/ventaja, probabilidades, proyecciones por
periodo, Head-to-Head y Forma Reciente. No se copian coeficientes ni resultados NBA.

El adaptador no inventa confianza, comparación de temporada, tendencia, descanso,
probabilidades por cuartos no consultados ni métricas de apuestas. Euroliga muestra
NO_CERTIFICADO, RAW, push y ventaja de regulación —no moneyline con OT—. Sus descriptivos
recientes proceden solo de la muestra conservada: V/E/D **en regulación**, medias
anotadas/recibidas y balance; no son victorias FT cuando hubo empate antes de OT.
H2H puede incluir prórroga y no se compara con líneas de regulación o de un cuarto.
Los datos ausentes aparecen N/D. Los acordeones usan IDs únicos en el historial.

La tabla común ordena Q1–Q4 y total. Las advertencias en texto humano no se duplican
como código y mensaje. Los históricos mantienen su fecha, línea y porcentajes
originales; adaptar la vista no recalcula ni reescribe el análisis.

## Controles

36 pruebas backend focalizadas y 58 frontend aprobadas; lint/build aprobados.
Se validan entradas, suma de medias observadas/pendientes, varianza restante,
inmutabilidad del modelo, ausencia de calibrador/ajustes PRE, no registro de cortes
como apuestas/PRE, despacho de rutas y rechazo de respuestas tardías tras limpiar.
También orientación H2H, empates en regulación, datos faltantes y presentación Euro
por el renderer compartido, sin llamadas NBA.

Las ejecuciones POST son sintéticas o con servicios simulados. No se usa Neon como
BD de pruebas ni se genera análisis productivo para capturas. El navegador muestra
NBA por cierre sin rellenar marcadores ficticios y reabre una captura Euro ya
existente. Los controles globales backend/PostgreSQL/Compose se verifican en CI.
Evidencia externa: `MODOS_NBA_Y_RESULTADOS_BALONCESTO_2026-10-22/`.
