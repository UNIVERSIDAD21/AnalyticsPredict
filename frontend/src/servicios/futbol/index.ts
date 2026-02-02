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
} from './equipos';

// Partidos
export {
  obtenerPartidosProximos,
  obtenerPartidosRecientes,
  obtenerPartido,
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
