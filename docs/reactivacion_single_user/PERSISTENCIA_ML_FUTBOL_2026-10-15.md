# Persistencia y serving ML fútbol — 2026-10-15

**Cierre técnico, no recertificación analítica.** Se reparó el ciclo de coeficientes,
registro, activación y recarga contra el contrato canónico. En Neon se ejecutaron
solo lecturas: **0 versiones fútbol**, sin entrenamiento/activación/calibración.
Las pruebas de publicación/activación y sus fallos usan PostgreSQL desechable.

## Fallos observados y correcciones

- El gestor consultaba `tipo_modelo`, ausente de la tabla real. Ahora usa
  `mercado_principal` (`CORNERS_FT`, `GOLES_FT`, `DISPAROS_FT`), versión entera y
  `metadata` JSONB existente; no necesita DDL ni rutas de archivos almacenadas en BD.
- El CLI perdía los modelos y solo intentaba guardar métricas con argumentos
  incompatibles. Ahora conserva coeficientes y dataset efectivo, publica un lote
  atómico y vuelve a cargarlo para comprobar igualdad. Guardar no activa por defecto.
- La carga por defecto creaba objetos vacíos. Ahora lee todas las versiones activas
  en un único snapshot SQL de solo lectura, valida cada familia y no sirve artefactos
  incompletos/corruptos/ambiguos. Cada análisis construye su predictor; no muta uno
  compartido por otra petición ni requiere reiniciar para observar activaciones.
- El artefacto JSON formato1 contiene contrato de features, dominio, targets,
  coeficientes, índices, residuales, ajuste UTC, métricas y dataset. SHA-256 completo
  en metadata; el campo `hash_datos` conserva sus 32 caracteres y se coteja con el
  prefijo del hash completo del dataset. El hash detecta incoherencias, no acredita
  autenticidad del proveedor ni disponibilidad histórica del dato.
- NPZ contiene el mismo JSON con `allow_pickle=False`. Legacy sin contrato explícito
  se rechaza; no se transforma silenciosamente en modelo apto.
- Activación valida versión/familia/hash antes de desactivar la anterior, dentro
  de transacción y lock por familia. Un fallo de otra familia revierte todo el lote.
- Equipos desconocidos no se predicen como un vector one-hot vacío. El serving
  persistido rechaza el uso retrospectivo de un modelo ajustado después del cutoff
  del partido; no equivale a una validación temporal ni recupera disponibilidad histórica.
- El nuevo artefacto es **raw**, sin calibrador vinculado. No reutiliza un calibrador
  de otra versión por coincidir mercado; no activa calibradores ni promoción beta.

## Dataset efectivo, no imputado

Consulta `FINALIZADO AND valido IS TRUE`, competición y UUID de temporada opcionales,
y cutoff exclusivo con medianoche UTC explícita (sin depender del TimeZone de BD).
Por familia exige sus cuatro targets: enteros no negativos, tiros al arco ≤ totales
y tiempos coherentes con el total cuando está observado. `NULL` nunca significa cero;
el cero deportivo observado se conserva. Excluye IDs duplicados y aplica poda iterativa
por mínimo de partidos por equipo. Hash sobre identidades, fechas y valores usados.
Cuenta partidos únicos; dos perspectivas son dos filas de diseño, no dos partidos.

Diagnóstico real de solo lectura, mínimos100 partidos/5 por equipo, sin las tres
copas europeas excluidas por la configuración legacy:

| Familia | Partidos efectivos | Equipos | Último dato | Exclusiones de candidatos |
|---|---:|---:|---|---|
| Corners | 14.136 | 186 | 2026-03-22 | 2.908 targets ausentes; 496 por mínimo de equipo |
| Goles | 10.716 | 302 | 2026-03-22 | 5.158 ausentes; 1 inválido; 1.665 por mínimo |
| Disparos | 14.379 | 191 | 2026-10-12 | 2.610 ausentes; 551 por mínimo |

Hay masa técnica para ajustar; **no** demuestra frescura por tiempos, calidad temporal,
calibración ni eficacia. Los 200 FT nuevos no completan corners/goles1T/2T. No se
reentrenó el histórico para simular una actualización reciente.

## API y UI

`/api/futbol/metricas/modelos` (y alias `/modelo`) ya no crea tres modelos de ejemplo,
MAE ni próximo reentrenamiento ficticios. Sin versiones devuelve lista vacía, fecha
futura `null` y estado explícito; fallo de almacén503 sin detalles privados. Solo
expone artefactos activos verificables y distingue si coinciden con la última carga
real. `/resumen` no presupone modelo activo. `/operacion` separa registro y carga,
sin inicializar predictor, escribir o entrenar por consultar.

Métricas faltantes permanecen N/D hasta el cliente. Las de ajuste se rotulan
`AJUSTE_IN_SAMPLE_NO_VALIDACION`; la UI no las califica como modelo validado ni
excelente aunque el R² de ajuste sea alto. La beta y los gates científicos no cambian.

## Rutina explícita

Desde `backend/`, salidas fuera del producto:

```bash
# Solo SELECT; no entrena por defecto.
.venv/bin/python scripts/entrenar_futbol.py --salida /RUTA_EXTERNA/dataset.json
# Ajustar sin publicar; acotar competición/temporada/cutoff según objetivo.
.venv/bin/python scripts/entrenar_futbol.py --entrenar --familia disparos --fecha-corte 2026-10-16
# Publicar coeficientes en BD, INACTIVOS por defecto.
.venv/bin/python scripts/entrenar_futbol.py --entrenar --familia disparos --guardar
```

`--activar` requiere `--guardar`, que requiere `--entrenar`. La activación técnica
no promociona mercados. `--competicion` y `--temporada-id` son repetibles. El flag
legacy `--validar`, que no ejecutaba lo prometido, se retiró: no se etiqueta el MAE
de ajuste como resultado de validación. Próximo trabajo científico: ventanas
train/cal/eval agrupadas por partido, baseline e intervalos, sin compartir las dos
perspectivas de un evento entre train/eval; después calibración ligada a versión.

## Evidencia y límites

- Suite global local: **771 passed, 0 failed, 0 skipped**, dos deprecaciones heredadas.
- Frontend: **24 pruebas**, lint y build verdes.
- HTTP real: cinco GET backend200 y `/operacion` frontend200. Sin modelo fútbol,
  sin próximo entrenamiento programado, resumen `modelo_activo=false`.
- Nueve huellas históricas idénticas al cierre previo y después de los GET;
  12 capturas NBA PRE/0outcomes y 0versiones fútbol intactos.
- Evidencias externas: `Carpeta de Entregas de Borlty/PERSISTENCIA_ML_FUTBOL_2026-10-15`;
  publicación/CI y estado final se registran en su acta, sin secretos.
- Pendientes: entrenamiento/evaluación explícitos por familia y ventana, frescura
  1T/2T, outcomes NBA futuros e independientes, KPI residuales y procedencia P&L.
  Visual local conserva su bloqueo anterior. **NO CERTIFICADO**.
