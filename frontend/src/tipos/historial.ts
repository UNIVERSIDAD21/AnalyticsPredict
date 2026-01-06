/**
 * historial.ts — Tipos para historial de partidos de equipos
 */

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
