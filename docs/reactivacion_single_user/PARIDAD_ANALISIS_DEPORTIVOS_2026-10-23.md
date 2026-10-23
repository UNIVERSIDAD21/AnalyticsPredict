# Análisis completo Euroliga y fútbol — 2026-10-23

## Alcance

Por instrucción del propietario se habilitan los mismos apartados de NBA aunque
el método no esté certificado: ganador, proyección por periodo, impacto de ajustes,
ajustes aplicados, valor, decisión/riesgo, H2H, forma, historial y razones.
Se conservan las rutas `/baloncesto` (selector Euroliga) y `/futbol`, el formulario
compartido y Bitácora. No se activan modelos ML de fútbol ni se cambian artefactos.

`analisis_integral` es un contrato adicional de los dos endpoints. El organismo
compartido lo presenta sin usar cálculos ni endpoints de NBA. El estado de calidad
se informa, pero no oculta el histórico, el contexto ni las nuevas secciones.

## Euroliga

- Predicción Ridge original conservada en `salida_modelo_base`; la respuesta
  primaria, las probabilidades presentadas y el snapshot de Bitácora usan el
  mismo escenario contextual. Se conserva la versión de la explicación.
- Forma: referencia = media de ataque propio y defensa rival de sus últimos diez
  finales previos. Desplazamiento = `(referencia − Ridge) × 0,25 × n/(n+20)`, con
  `n=min(muestras propias, rivales)` y tope de ±4 puntos por equipo.
- Descanso por fechas: −0,75 puntos con un día entre partidos; −0,35 con dos días;
  cero en otro caso. No acredita horas completas de recuperación.
- Ajustes de partido repartidos uniformemente entre cuatro cuartos. Se conserva
  sigma Ridge: no se ha validado la dispersión después del ajuste. La localía ya
  está dentro de Ridge; no se suma de nuevo. Sin lesiones/alineaciones imputadas.
- Ganador: aproximación gaussiana discreta del margen de 40 minutos, con empate
  separado. No predice al ganador de la prórroga ni es moneyline con OT.
- Cortes live no reciben estos ajustes adicionales. Los archivos anteriores se
  enriquecen solo en memoria, sin cambiar sus salidas ni reescribir sus bytes.
- Cuotas Over/Under se pueden introducir antes de analizar y en el escenario
  de valor. La cuota que se guarda debe confirmarse en el modal de Bitácora.

La EVAL histórica del candidato Ridge no valida este escenario contextual nuevo.

## Fútbol

- El endpoint ya calculaba heurística y Dixon-Coles/ensemble aun sin ML activo.
  Se expone el 1X2 completo (incluido empate) siempre por goles a 90 minutos más
  añadido, independientemente del mercado elegido de goles/córners/disparos.
- Proyecciones 1T/2T/FT y por equipo tomadas de los mercados propios del endpoint.
  Se elimina el reparto visual ficticio 48/52 y la desviación individual inferida.
  Los periodos se estiman de forma independiente: FT no necesariamente es su suma.
- Trazas aditivas reales de forma y localía para los totales FT que ya ajustaba el
  motor; diferencia heurística/ensemble por mercado cuando existe. No se adjudica
  un delta ficticio a factores que están integrados en el estimador base.
- Balance V/E/D y racha por goles; medias del H2H y forma por la métrica elegida.
  No se fabrican confianza, días de descanso ni una media de temporada completa
  a partir de la ventana corta cargada.

## Valor y riesgo

Con una cuota decimal válida, EV por unidad = `p(acierto) × (cuota−1) − p(fallo)`;
push devuelve la unidad. Precio de equilibrio = `(1−p(push))/p(acierto)`.
Con ambas cuotas se normalizan inversas para quitar el margen; el edge se compara
con la probabilidad condicional a no-push. Se muestra desviación del retorno,
probabilidad de fallo, push y lectura matemática positiva/negativa/equilibrio.
No se produce stake ni una recomendación automática.

Sin cuota válida, el escenario permanece editable en lugar de desaparecer.
En líneas enteras de fútbol donde el contrato legacy no separa masa de push, no se
declara push cero ni se calcula un EV ficticio. Las probabilidades conservadas por
el motor permanecen visibles; esta limitación no oculta las demás secciones.

## Verificación

Regresiones matemáticas/contratos y formulario Euroliga, pruebas frontend,
lint/build/auditoría de dependencias de producción. Vista sintética auténtica
rotulada en 1440 y 390 px; sin overflow ni requests de análisis/productivos.
No se envió POST productivo, no se ingresaron datos, no se entrenó ni se activó un
modelo y no se creó una apuesta. Huellas y logs se conservan en entrega externa.
El detalle final de pruebas/CI corresponde al SHA publicado, no a un run previo.
