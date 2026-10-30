# Continuación de mejoras locales — 2026-10-30

Orden vigente: continuar el catálogo completo, sin detenerse en el primer lote.
Esta continuación no declara las treinta mejoras terminadas ni activa modelos.

## Uso personal

- Favoritos de **equipos, ligas y competiciones**, separados del favorito de una
  consulta y de los partidos guardados en Bitácora. Gestión/exportación en Cuaderno.
  Identidad liga/tipo/ID; si Base local no tiene ID de BD, conserva un favorito por
  nombre explícitamente distinto. No se adivinan equivalencias entre catálogos.
- Hoy filtra **la página recibida**, con conteo visible/recibido y sin afirmar
  cobertura del calendario completo. Cambiar favoritos no consulta ni ingiere.
  Los errores de almacenamiento no sobrescriben preferencias anteriores.
- Ficha fútbol: agenda plegada tras seleccionar, configuración y resultado
  principales, seguimiento en BD opcional. Plegar no desmonta/reconsulta el catálogo.
  Temporadas, elegibilidad, cancelación y reconstrucción conservan su contrato.
- Todos los resultados compartidos exponen versión, emisión, modo, dataset,
  corte del modelo/corte exclusivo de consulta y convención OT. Ausencias N/D.
  WNBA conserva los metadatos de fuente que el adaptador antes no trasladaba.
- Comparador Euroliga usa parámetros originales de esa corrida y su normal
  **discretizada**, con push en enteras. No reutiliza el comparador continuo NBA.
  CDF aproximada, no nueva salida API ni probabilidad calibrada. WNBA Sobol/OT y
  mezclas de fútbol no se reconstruyen a partir de solo media/desviación.
- Laboratorio abre un informe experimental JSON local validado, sin subirlo ni
  convertirlo en modelo. Tablas comunes y de cobertura ampliada separadas. No
  acredita autenticidad del archivo, activación o validez futura de las métricas.

## Desarrollo WNBA: resultado observado

El artefacto original preserva 1.997 finales normalizados de2019–2026. Se usaron
solo REG. Euroliga no conserva los targets completos dentro de su artefacto;
NBA tampoco aporta el snapshot completo necesario para un benchmark nuevo.

[Política declarada antes de medir](PROTOCOLO_CONTRACCION_WNBA_2026-10-30.json):
TRAIN anterior a2024; CAL selección hasta15jul2024; CAL dispersión hasta2025;
EVAL2025–corte original. Recencias uniforme/365/730 y contracción0/8/24. Nueve
variantes sobre la misma selección. Ninguna selección usa EVAL ni la CAL de
residuos; no refit final. **EVAL ya se había observado**, no test intacto.

- Se reprodujeron sin ajustar las450 predicciones del candidato original, delta0.
- CAL seleccionó semivida730 y **k0**, sin contracción adicional. En el soporte
  común de450 partidos, MAE total15,295 frente a15,295 original y15,321 media de
  liga. Delta numérico≈1e-14: redondeo, **no mejora estadística**.
- El prior de liga permitió calcular616/616 frente a450/616 del gate original.
  Los166 adicionales tienen equipos sin historial TRAIN; no se les inventa muestra.
  MAE ampliado15,684 frente a15,782 media de liga sobre esos mismos616.
- En esos166, cobertura del intervalo nominal80%:72,89%; total16,737MAE.
  En el común:76,67% de cobertura. Dispersión RAW, no calibración probabilística.
  **No justifica retirar gates ni servir el fallback**. No mejoras de equipos
  nuevos acreditadas en Euroliga ni trasladadas entre ligas.

El candidato, coeficientes/mapping/orden, covarianza, selección, todos los pares,
abstenciones, referencias y protocolo/hash quedan en el informe externo. La cohorte
original se conserva íntegra. No publicaciones activas, journals, ingestas o BD
de aplicación modificados. La evaluación tampoco certifica el refit publicado.

Reproducción, desde cualquier carpeta, con Python del entorno preparado:

```text
python backend/scripts/evaluar_contraccion_wnba.py --publicacion <copia íntegra WNBA> --salida <archivo JSON externo NUEVO>
```

Rechaza sobreescritura, origen dañado/corte futuro y salida dentro del repositorio.
Un hilo. No red/BD; la instrumentación adicional observó cero intentos externos.
Antes de promoción necesitaría una política nueva y evidencia futura congelada;
la política define mínimos, pero no se ha creado esa cohorte ni programado tareas.

## Validación y continuidad

367 backend aprobadas,0 fallos/omisiones con PG18 sintético propio55434 detenido.
152 frontend aprobadas, lint/TypeScript/build aprobados. El intento anterior
mezcló fuentes editadas durante la ejecución; FINAL_V2 con código congelado es
el recibo autoritativo, sin pruebas omitidas ni fallos.
Seis vistas verificadas: cuatro con API/artefacto originales sin BD y dos de
fútbol con GET **sintéticos rotulados**. No E2E contra datos deportivos de BD.
Una sola consulta NBA técnica arbitraria; favoritos, copias e informe no repiten
POST.0 errores JS/overflow;38 archivos de estado intactos.

Entrega externa `CONTINUACION_MEJORAS_USO_LOCAL_2026-10-30`, distinta del primer
recibo. Conservar ambos. Fuente Neon rechazada por cuota en la comprobación previa;
no reintentos repetidos. Migración PREPARADO_NO_MIGRADO; el paquete original no se
sobrescribe. V4 solo podrá continuar con desarrollo y cohortes originales.
