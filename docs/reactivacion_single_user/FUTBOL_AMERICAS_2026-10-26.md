# Fútbol Américas — contrato de incorporación local

Fecha de trabajo: 2026-10-26. Código **local, no publicado**. No confundir el
commit Git anterior con estos cambios ni atribuirles su CI remota.

## Alcance y estado de la operación

Integración autorizada de MLS, Argentina, Colombia y Brasil en el flujo existente
`/futbol`. Las tres etapas tienen aplicación SQL confirmada y postflight
independiente: **13.790 finales válidos y 123 fixtures**, 13.913 registros, sin
actualizaciones de filas anteriores. Repetición READ ONLY: cero cambios.

| Competición | Finales | Fixtures |
| --- | ---: | ---: |
| MLS | 3.740 | 44 |
| MLS is Back — eliminatorias | 15 | 0 |
| Primera División Argentina | 2.841 | 18 |
| Copa Diego Armando Maradona | 135 | 0 |
| Copa de la Liga Profesional | 786 | 0 |
| Copa de la Superliga | 60 | 0 |
| Categoría Primera A | 3.237 | 39 |
| Brasileirão Série A | 2.976 | 22 |

Colombia recorrió 94/94 meses, estado fuente COMPLETO_CON_INCIDENCIAS, tres
pendientes estadísticos (564831, 564839 y 626317) conservados como parciales.
690704 se apartó por falta de desglose acreditado de la tanda, no porque su
marcador FT 2–1 fuera falso; 730479 está abandonado. Brasil terminó naturalmente,
sin duplicarlo; cinco cuarentenas históricas, incluida una por estado desconocido.
El calendario tiene horas confirmadas hasta 7-nov MLS, 2-nov Argentina, 9-nov
Colombia y 6-nov Brasil; no acredita publicación oficial íntegra hasta diciembre.

La evidencia verificable está fuera del repositorio, en la entrega privada
`INTEGRACION_FUTBOL_AMERICAS_2026-10-26`: planes congelados, respaldos completos,
restauraciones, ensayos con rollback, recibos y censos de campo/objetivo.

## Identidad y datos

- Tablas canónicas existentes: países, competiciones, temporadas, equipos y
  partidos de fútbol; relaciones ESPN exactas por equipo, feed/temporada y
  feed/evento. No se requirió DDL ni migración productiva.
- Competiciones: `USA_MLS`, `USA_MLS_BACK`, `ARG_PRIMERA`, `ARG_MARADONA`,
  `ARG_COPA_LPF`, `ARG_SUPERLIGA`, `COL_PRIMERAA`, `BRA_SERIEA`.
- Un feed no equivale a un torneo: la Copa Maradona y las eliminatorias de MLS
  is Back tienen identidad propia; los All-Star quedan fuera. El agregado
  argentino se ingiere una vez, no junto con sus copias por torneo.
- Temporadas según la fuente, no según el año del kickoff: una temporada
  brasileña 2020 puede tener encuentros jugados en 2021. Las temporadas
  argentinas cruzadas conservan su denominación.
- Cada CSV se coteja con el JSONL y los hashes del reporte. Duplicados,
  contradicciones, identidades ambiguas y estados no finalizados se separan.
  Se preserva el original completo en JSONB, incluidos regulación, ET y tanda.
- `NULL` permanece desconocido; cero observado permanece cero. Seis campos FT
  completos de córners/tiros/SOT no acreditan las mitades ni todas las métricas.
  La ausencia de córners por tiempo deja únicamente esos objetivos en N/D.
- El esquema legacy denomina `datos_completos` a la presencia de goles FT;
  no usar esa bandera como prueba de integridad estadística.

## Ingesta y calendario

`backend/ingesta_futbol_americas.py` no hace HTTP, DDL, borrados ni commits.
`scripts/importar_futbol_americas.py` es READ ONLY por defecto. La aplicación
requiere plan y respaldo íntegros; la operación entregada añade restauración en
PostgreSQL propio, ensayos exactos con rollback, guardas de antes-imagen, locks,
huellas de tablas protegidas, commit único y postflight READ ONLY campo a campo.
Las operaciones confirmadas no se repiten; la comprobación idempotente no hace
DML. Un final existente distinto exige conciliación explícita, no se sobrescribe.

`scripts/preparar_calendario_americas.py` reutiliza el transporte/normalizador
LATAM y el control de red compartido, de forma serial. Consulta los meses que
intersectan 26-oct–26-dic inclusive en Colombia. Solo acepta fixtures programados
con equipos, instante y competición acreditados, sin goles ni estadísticas.
Las fechas/horas no confirmadas se conservan en cuarentena externa: no se
inventan medianoches. Un feed vacío o una fecha máxima no certifican publicación
oficial íntegra. Los calendarios son snapshots fechados, no refresco automático.

## API e interfaz

- `GET /api/futbol/competiciones/{id}/temporadas`: temporadas y conteos reales.
- `GET /api/futbol/partidos/catalogo`: competición obligatoria, temporada
  opcional, modo `historicos`/`proximos`, paginación y ventana futura acotada.
- Historial detallado y H2H aceptan competición y corte exclusivo; la pantalla
  los usa con el mismo ámbito que el cálculo. El detalle devuelve IDs canónicos
  de torneo y temporada, y permite omitir agregados globales innecesarios.
- `POST /api/futbol/analizar` admite `modo_historico` y `solo_consulta`. Una
  reconstrucción exige un final válido, corta estrictamente antes de su kickoff,
  no carga ML actual y no registra emisiones, recomendaciones ni apuestas.
- Nuevas competiciones usan `heuristico-americas::1.0.0`, reutilizando fórmulas
  y elegibilidad existentes con histórico exclusivo de su propio torneo.
  Fuerzan transacción READ ONLY y no heredan modelos, calibradores ni métricas
  de las competiciones anteriores.
- `CatalogoFutbol` cambia consultas reales, temporadas, fixtures e histórico;
  cancela cargas y descarta respuestas tardías al cambiar ámbito. Los enlaces
  por `partidoId` resuelven su propia competición/temporada, no la liga inicial.
- Se conserva la presentación compartida: modo histórico explícito, kickoff y
  consulta separados, horas COT y advertencia RAW. Sin guardado de apuestas ni
  combinadas históricas. Un calendario vacío no oculta la consulta histórica.

## Evidencia predictiva

`scripts/evaluar_heuristico_americas.py` llama al analizador real en un clon local
congelado. Protocolo `americas-heuristico-walkforward-v1`: finales 2025–2026 o, en
torneos retirados, último 20% de instantes; datos anteriores al kickoff, mismo
torneo y temporadas registradas. Referencia: media y frecuencia Over de los
730 días previos, mínimo 40 observaciones elegibles. Se separan outcome ausente,
abstención del estimador y referencia insuficiente. Comparación emparejada de
MAE/RMSE/sesgo/Brier/logloss por objetivo, no rentabilidad.

Evaluados 3.686 encuentros, 56 grupos torneo–mercado. Resultados mixtos, sin
superioridad general demostrada. Por ejemplo, GOLES_FT: MAE Colombia 1,2470 frente
a 1,2316 de referencia; Brasil 1,2505 frente a 1,2312. No se ajustan parámetros
con EVAL, no se activa un nuevo ML y no se declara calibración. La descarga
posterior no acredita disponibilidad original ni predicciones prospectivas.
Las métricas no certifican cualquier selección distinta de temporadas.

Backend final: 1.709 pruebas aprobadas, cero omitidas; frontend: 122 aprobadas,
lint/build y auditoría de producción sin vulnerabilidades conocidas. API real
histórica/futura en las ocho competiciones, incluidos N/D y ámbitos de historial.
UI auténtica en escritorio/móvil. No se atribuye a estos cambios la CI de HEAD.

## Límites y conservación

Sin cron, apuestas financieras, recalibración, activación de modelos o cambios
de NBA/WNBA/Euroliga. Los scrapers ajenos y artefactos/journals previos se comparan
con el baseline. El servicio local continúa disponible; la publicación Git y
el CI remoto quedan fuera de esta operación.
