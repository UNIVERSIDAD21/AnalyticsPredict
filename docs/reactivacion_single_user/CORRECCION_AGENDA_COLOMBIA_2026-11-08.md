# Agenda colombiana: conflictos y confirmación oficial

## Causa acreditada

El scoreboard ESPN `col.1` de noviembre de 2026 publica diez cruces a las
15:30 COT del día 8, además de los partidos reales de esa jornada. Varios clubes
aparecen dos veces en menos de 24 horas; `timeValid=true` no evita el error.
El importador validaba cada identidad por separado, no la compatibilidad del
calendario completo. Además, `/proximos` no filtraba `valido`, aunque `/agenda`
y el catálogo sí lo hacían.

DIMAYOR confirma para el 8 de noviembre: Santa Fe–Pasto 14:00,
Jaguares–Bucaramanga 16:05, Tolima–Millonarios 18:10 y Alianza–Llaneros 20:15.
Junior–Cúcuta queda el 9 de noviembre a las 19:00, siempre America/Bogota.
Fuente: <https://dimayor.com.co/>. Es un corte observado, no un fixture perpetuo.

## Contrato

- El planificador compara todos los eventos colombianos del lote con el
  calendario vigente, incluyendo resultados recientes y equivalencias exactas
  de clubes, ID fuente y temporada. No hace fuzzy matching.
- Un club con dos partidos distintos en menos de 24 horas produce una
  incidencia, no una hora certificada. La confirmación oficial exacta y los
  finales se conservan. Si ambos candidatos son ambiguos, no se escoge uno.
- Los programados afectados sin marcador se conservan con `valido=false` y
  evidencia `COL_AGENDA_CONFLICTO_V1` en `horarios_futbol`. No se borran, no
  se inventa otra fecha y no se confunde cuarentena con cancelación/aplazamiento.
- Una captura idéntica no los reactiva. Solo una cuarentena creada por este
  contrato admite recuperación automática, con hora distinta, captura posterior,
  identidad intacta y ausencia de nuevos choques. Invalidaciones ajenas y finales
  no se rehabilitan por esta vía.
- La evidencia oficial conciliada queda en `confirmacion_agenda`, con URL,
  observación, hash, instante y clubes. ESPN no puede desplazar ese horario.
  Una discrepancia posterior necesita conciliación oficial; no se aplica el
  principio de que la captura más nueva siempre gana.
- El calendario genérico tampoco desplaza metadatos horarios de finales
  colombianos ya conciliados. Los campos NULL de resultados mantienen su
  tratamiento previo, sin modificar goles observados.
- La lista de próximos filtra la misma validez tanto en filas como en el total.

## Alcance y operación

No incorpora un scraper oficial permanente, no certifica todo el histórico ni
todas las programaciones futuras y no cambia resultados, estadísticas, modelos,
entrenamiento ni seguimiento personal. El botón normal carga la guarda en su
siguiente subproceso. El cambio en la ruta HTTP exige recargar solo el backend.
No se crea automatización, vigilancia ni una actualización multiliga adicional.

Pruebas: contratos puros, SQL sintético, replay sin cambios, rehabilitación
controlada, exclusión por API, clon íntegro con rollback y fallo intermedio.
Evidencias operativas y respaldos permanecen fuera del repositorio del producto.
