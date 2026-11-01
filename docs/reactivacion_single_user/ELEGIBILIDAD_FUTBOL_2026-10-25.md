# Elegibilidad de fútbol por objetivo — entrega local

Estado: implementado en el checkout, **sin commit, push ni CI remoto de este diff**.
Orden del propietario: implementar la elegibilidad propuesta y continuar con
mejoras adicionales comprobables. No inicia ingestas, descargas, migraciones
productivas, entrenamiento ni activación/publicación de modelos.

## Contrato

`futbol-elegibilidad-por-objetivo-v1` clasifica observaciones como `OBSERVADO`,
`AUSENTE`, `INVALIDO` o `ESTIMADO`. Cero es dato presente; NULL no se convierte en
cero. Valores negativos, no enteros/no finitos y conflictos explícitos se apartan
del objetivo afectado, sin modificar las filas canónicas.

- `calidad/elegibilidad_futbol.py` es el criterio compartido por los resúmenes
  estadísticos del análisis, el inventario y los DTO históricos.
- Un total histórico requiere ambos lados; el contexto individual usa el lado
  del equipo, con denominadores separados. No se mezclan las muestras H2H, sede,
  todas las sedes y competición.
- Los mínimos H2H=5, casa=25 y fuera=25 son avisos contextuales, no acreditación
  de calibración ni bloqueo global. Sin observaciones utilizables del equipo
  requerido, solo ese mercado se omite de las predicciones/recomendaciones y de
  su registro; su elegibilidad permanece explícita y su objetivo responde N/D.
- Los FT individuales se calculan desde FT, no sumando mitades ausentes.
- Goles FT utiliza regulación: en ET explícita se resta el desglose de goles ET;
  si no está acreditado, N/D. No se divide el FT para fabricar mitades. Córners y
  tiros FT con ET sin desglose estadístico se excluyen de regulación. Los parciales
  observados siguen siendo independientes si sus valores son coherentes.
- Tiros 1T/2T son el reparto heurístico existente desde FT, etiquetado `ESTIMADO`,
  con cero observaciones de tiros por mitad. Los periodos de córners/goles sin
  soporte no se usan como inputs ficticios de ese reparto; se conserva su ratio
  predeterminado explícito cuando falta contexto. No es calibración.
- El ganador 1X2 tiene soporte propio de goles FT; sin él queda N/D aunque haya
  córners o tiros calculables. Una falla de consulta histórica devuelve 503, no
  una muestra vacía ni estimaciones desde cero.

La API añade `elegibilidad_mercados` y `objetivo.calidad_datos.elegibilidad`;
se preserva el contrato previo de objetivos y grillas calculables. El frontend
conserva NULL en media, dispersión, probabilidades y riesgo. La tabla del análisis
explica observados/estimados/ausentes/inválidos y motivos por contexto.

## Estado y denominadores

`/operacion` añade inventario por mercado/periodo y selector de temporada en cada
competición de fútbol. Goles FT usa todos los finales válidos anteriores al corte;
los otros objetivos usan finales con ambos goles FT. Se muestran por separado los
finales sin marcador y los NULL literales del inventario previo. Ausente en la
nueva capa también puede significar regulación sin acreditar, no solo NULL.

Los códigos guardados no están recertificados contra una fuente externa; no se
recategorizaron copas ni se declararon datos verdaderos por tener presencia.
El cursor procesa bloques acotados y reutiliza clasificaciones por campo; el
inventario no carga ni entrena un predictor.

## Mejoras adicionales

1. H2H e historial de equipo comparten normalización por campo, exponen goles por
   mitad, excluyen filas invalidadas/futuros y conservan NULL. Sus transformadores
   frontend comparten implementación. No se usa FT como sustituto de una mitad.
2. Los paneles históricos omiten campos ausentes de sus promedios. Sin forma
   reciente utilizable se presenta ausencia, no promedios 0–0 ni tendencia estable.
3. Estado compara finales NBA posteriores al último dato con la versión registrada,
   el dominio de cuartos válidos y las temporadas efectivas. Separa PRE excluida de
   nuevos resultados REG/POST dentro del alcance. No dice «actualizado» por una
   fecha global ni reentrena; un registro de versiones ausente/incompatible es N/D.

## Verificación y límites

Regresiones puras, API sintética y PostgreSQL desechable cubren NULL/cero, negativos,
periodos incompatibles, ET, soporte por lado, FT con mitades ausentes, estimaciones,
falla de contexto, preservación de mercados independientes y contrato de registro.
Pruebas frontend cubren N/D, tablas por temporada y ausencia de forma/historial.
La integración de prospectiva mantiene su snapshot READ ONLY con una fixture que
incluye las columnas del inventario ampliado.

Evidencia externa: `Carpeta de Entregas de Borlty/ELEGIBILIDAD_MERCADOS_FUTBOL_2026-10-25/`.
El informe final registra los resultados medidos, capturas reales de Estado y banco
sintético rotulado, integridad y límites. No atribuir la CI anterior de HEAD al diff
local. No se acredita precisión, calibración, integridad oficial de calendarios ni
la verdad externa de cada campo por esta implementación.
