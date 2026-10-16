# KPI de calibración: cohorte, N/D y frescura — 2026-10-16

## Alcance cerrado

Subbloque de M04, no cierre de toda la capa KPI ni recertificación. Reparación de
`GET /api/metricas/calibracion` y `GET /api/metricas/calibracion/{mercado}/curva`,
su calculador y la pantalla de métricas. Sin DDL/DML ni precálculos en Neon.

| Hallazgo reproducible | Corrección |
|---|---|
| Curva mezclaba calibradas con fallback raw por fila | `serie=raw|calibrada`, raw por defecto; sin fallback. Calibrada requiere `calibrador_id` |
| Resumen podía mostrar n raw junto a métrica calibrada de otra cohorte | n seleccionado, n_raw, n_calibradas, exclusiones por probabilidad y base_rate de la misma serie |
| Mejora atribuida entre muestras distintas | Comparación solo si coinciden las filas con ambos pares válidos; ni igual n ni cobertura parcial bastan |
| Curva vacía devolvía ECE/MCE0 | `null`, estado NO_EVALUABLE; UI sin gráfica ni etiqueta de calibración perfecta |
| Caché300s sin revisión/invalidation y timestamp de respuesta nuevo | Cachés retiradas de estos dos GET; cálculo bajo demanda y hora UTC explícita |
| Error capturado se presentaba como éxito/n0 y texto del driver | HTTP503 con mensaje estático y log solo de tipo de excepción |
| Sharpness calculaba desviación, no varianza del catálogo | Varianza poblacional; prueba .2/.8 => .09, no .3 |
| UI ocultaba n pequeño y diagnosticaba excelencia/drift por un ECE aislado | Conteos/métricas descriptivos visibles, muestra pequeña explícita, sin inferir drift/eficacia |

## Contrato de lectura

Ambos GET comparten origen obligatorio, periodo, serie y `modelo_version_id`
opcional positivo. Sin versión se expone agregado descriptivo de todas las
versiones, no una validación de una versión concreta. La curva conserva tipo y
número de bins solicitados. Raw/calibrada mantienen distintas muestras cuando
falta cobertura; una probabilidad ausente/no finita/fuera de[0,1] se excluye de
su serie y cuenta. Push y outcomes0–0 tienen contadores separados.

`n_predicciones` del resumen y `n_predicciones_total` de la curva son el n de la
serie seleccionada. La marca de suficiente_data usa ese n, no el de otra serie.
`estado_calidad` distingue VALIDO_DESCRIPTIVO y NO_EVALUABLE; `certificacion` es
siempre NO_CERTIFICADO. `cache=SIN_CACHE` solo describe estos dos reportes, no
toda la aplicación. `calibrador_activo` describe el registro activo actual; no
se atribuye retrospectivamente a todas las filas del periodo.

Cambio intencional de contrato: default **raw**, antes resumen calibrado/curva
mixta; ECE/MCE nullable en curva. Cliente y tipos se actualizan juntos. El campo
interno `n_predicciones` del calculador batch conserva su significado raw; la API
selecciona el n correspondiente de forma explícita. No se migran precálculos viejos.

No hay snapshot global atómico entre solicitudes HTTP diferentes: una ingesta
concurrente puede cambiar los datos entre consultas. No se afirma una revisión de
datos que no existe. La igualdad SQL/API/curva se verifica sobre fixture estable.

## Pruebas y contraste real

- **794 backend passed**, cero fallos/skips, dos deprecaciones heredadas.
- **27 frontend passed**, lint/build verdes. Pruebas de filtros comunes, n pequeño
  visible, N/D, cero sin falsa excelencia y propagación de serie/versión.
- PostgreSQL sintético real: dos series, versión distinta excluida, calibrada sin
  ID, raw inválida, push y0–0; resumen/curva con mismos n/ECE/exclusiones. Todos los
  GET bajo transacción READ ONLY; huella de predicciones intacta.
- Dos lecturas consecutivas reflejan cambios sin esperar TTL; fallo de datos
  retorna503 sin valor falso ni texto del driver en respuesta/log.
- Contraste ASGI real con configuración protegida: **4/4 GET200**, todas sus
  conexiones READ ONLY, siete huellas intactas. Q1/API_USUARIO,2023-01-01→2026-10-16:
  raw368pares,8outcomes0–0excluidos, Brier0,21272/ECE0,04773 descriptivos;
  calibrada0pares y368sin probabilidad acreditada, Brier/ECE/MCE N/D.

ASGI no acredita servidor desplegado ni revisión visual de navegador. Estos368
pares históricos tampoco son prospectivos/independientes ni temporalmente
certificables por el hecho de producir una métrica numérica.

Evidencias externas: `KPI_CALIBRACION_CANONICA_2026-10-16` en Carpeta de Entregas
de Borlty (script read-only, respuestas agregadas/huellas y logs), enlazadas desde
el plan maestro. CI/commit se anotan en el acta, sin secretos.

## Residual explícito

M04 sigue abierto: P&L cross-sport/procedencia y otros KPI, consumidores, caches y
vistas físicas deben cotejarse por separado. Auditoría GET transitiva/observabilidad
integral corresponde a M05. No se declara revisada toda ruta por reparar estas dos.
No repetir vistas ROI legacy ya despublicadas ni pedir soportes que no existen.
