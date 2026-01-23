/**
 * historial.ts — Tipos para historial de partidos de equipos
 */

import type { Mercado } from './analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS BASE
// ══════════════════════════════════════════════════════════════

export interface PuntosPartido {
  q1: number;
  q2: number;
  q3: number;
  q4: number;
  ot: number;
  total: number;
}

export interface PartidoHistorial {
  id: string;
  fecha: string;
  temporada: string | null;
  equipoLocal: string;
  localAbr: string;
  equipoVisitante: string;
  visitanteAbr: string;
  ubicacionEquipo: 'LOCAL' | 'VISITANTE';
  puntosEquipo: PuntosPartido;
  puntosRival: PuntosPartido;
  resultado: 'VICTORIA' | 'DERROTA';
}

export interface PartidoHistorialAPI {
  id: string;
  fecha: string;
  temporada: string | null;
  equipo_local: string;
  local_abr: string;
  equipo_visitante: string;
  visitante_abr: string;
  ubicacion_equipo: 'LOCAL' | 'VISITANTE';
  puntos_equipo: PuntosPartido;
  puntos_rival: PuntosPartido;
  resultado: 'VICTORIA' | 'DERROTA';
}

export interface InfoEquipoHistorial {
  id: string;
  nombre: string;
  abreviatura: string;
  logo_url?: string | null;
}

export interface FiltrosDisponiblesHistorial {
  temporadas: { id: string; nombre: string }[];
}

export interface RespuestaHistorialEquipo {
  exito: boolean;
  equipo: InfoEquipoHistorial;
  total_partidos: number;
  partidos: PartidoHistorialAPI[];
  filtros_disponibles: FiltrosDisponiblesHistorial;
}

// ══════════════════════════════════════════════════════════════
// TIPOS PARA HISTORIAL DETALLADO (Sección de análisis)
// ══════════════════════════════════════════════════════════════

/**
 * Filtro de ubicación para partidos
 */
export type FiltroUbicacion = 'TODOS' | 'LOCAL' | 'VISITANTE';

/**
 * Opciones de cantidad de partidos a mostrar
 */
export type CantidadPartidos = 10 | 15 | 20 | 30 | 40;

/**
 * Tipo de racha actual
 */
export type TipoRacha = 'OVER' | 'UNDER' | 'MIXTA';

/**
 * Tendencia de puntuación
 */
export type TendenciaHistorial = 'SUBIENDO' | 'BAJANDO' | 'ESTABLE';

/**
 * Información de racha actual
 */
export interface RachaActual {
  tipo: TipoRacha;
  cantidad: number;
}

/**
 * Estadísticas agregadas de OVER/UNDER
 */
export interface EstadisticasOverUnder {
  /** Total de partidos analizados */
  totalPartidos: number;
  /** Cantidad de partidos OVER */
  partidosOver: number;
  /** Cantidad de partidos UNDER */
  partidosUnder: number;
  /** Porcentaje de OVER (0-100) */
  porcentajeOver: number;
  /** Promedio de puntos totales en el mercado seleccionado */
  promedioTotal: number;
  /** Diferencia promedio vs la línea ingresada */
  promedioVsLinea: number;
  /** Racha actual (consecutivos) */
  rachaActual: RachaActual;
  /** Tendencia (últimos 5 vs anteriores 5) */
  tendencia: TendenciaHistorial;
  /** Promedio de los últimos 5 partidos */
  ultimos5Promedio: number;
  /** Promedio de los 5 partidos anteriores */
  anteriores5Promedio: number;
}

/**
 * Configuración del historial para filtros
 */
export interface ConfiguracionHistorial {
  /** Cantidad de partidos a mostrar */
  cantidad: CantidadPartidos;
  /** Filtro de ubicación (local/visitante/todos) */
  ubicacion: FiltroUbicacion;
  /** Mercado seleccionado para análisis */
  mercado: Mercado;
  /** Línea ingresada para comparación O/U */
  linea: number;
}

/**
 * Partido con datos calculados para el mercado seleccionado
 */
export interface PartidoConMercado extends PartidoHistorial {
  /** Total de puntos según el mercado seleccionado */
  totalMercado: number;
  /** Resultado formateado según el mercado (ej: "28-24") */
  resultadoMercado: string;
  /** Si el total supera la línea */
  esOver: boolean;
  /** Diferencia entre el total y la línea */
  margenVsLinea: number;
}
