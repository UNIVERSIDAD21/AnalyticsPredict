/**
 * useFutbol.ts — Hook principal y exportaciones centralizadas para el módulo de fútbol
 *
 * Este archivo re-exporta todos los hooks relacionados con fútbol
 * para facilitar las importaciones desde un único punto.
 */

// Re-exportar hooks individuales
export { usePartidosFutbol } from './usePartidosFutbol';
export { useAnalisisFutbol } from './useAnalisisFutbol';

// Re-exportar tipos para conveniencia
export type {
  PartidoFutbolResumen,
  PartidoFutbolDetalle,
  FiltrosPartidos,
  AnalisisFutbolRequest,
  AnalisisFutbolResponse,
  ApuestaFutbol,
  ApuestaFutbolRequest,
  FiltrosApuestas,
  ResumenApuestasFutbol,
} from '../tipos/futbol';
