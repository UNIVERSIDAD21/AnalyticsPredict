/**
 * index.ts — Exportaciones de servicios de fútbol
 */

// Competiciones
export {
  obtenerCompeticiones,
  obtenerCompeticion,
  obtenerEquiposCompeticion,
} from './competiciones';

// Equipos
export {
  buscarEquipos,
  obtenerEquipo,
  obtenerEstadisticasEquipo,
  obtenerPartidosEquipo,
  obtenerPartidosEquipoDetalle,
} from './equipos';

// Partidos
export {
  obtenerPartidosHoy,
  obtenerPartidosProximos,
  obtenerPartidosRecientes,
  obtenerPartido,
  obtenerH2HPartidos,
} from './partidos';

// Análisis
export { analizarPartido } from './analisis';

// Apuestas
export {
  crearApuesta,
  obtenerApuestas,
  obtenerApuesta,
  actualizarApuesta,
  cancelarApuesta,
  resolverApuestas,
  obtenerEstadisticas,
} from './apuestas';

// Métricas
export {
  obtenerMetricasCalibracion,
  obtenerMetricasRendimiento,
  obtenerEstadoModelos,
  obtenerResumenSistema,
} from './metricas';
