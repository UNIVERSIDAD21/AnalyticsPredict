/**
 * estadisticas.ts — Tipos para estadísticas de equipos
 */

export interface RecordEquipo {
  victorias: number;
  derrotas: number;
}

export interface PromediosCuartos {
  q1: number;
  q2: number;
  q3: number;
  q4: number;
  total: number;
}

export interface PromediosEquipo {
  anotados: PromediosCuartos;
  recibidos: PromediosCuartos;
}

export interface RendimientoLocalVisitante {
  victorias: number;
  derrotas: number;
  ppg: number;
}

export interface TendenciasOver {
  q1: number;
  q2: number;
  q3: number;
  q4: number;
  total: number;
}

export interface EstadisticasEquipo {
  nombre: string;
  abreviatura: string;
  conferencia: string;
  record: RecordEquipo;
  posicion: number;
  racha: string[];
  promedios: PromediosEquipo;
  local: RendimientoLocalVisitante;
  visitante: RendimientoLocalVisitante;
  tendencias_over: TendenciasOver;
  linea_promedio: number;
}

export interface TemporadaDisponible {
  id: string;
  nombre: string;
}

export interface RespuestaEstadisticasEquipos {
  exito: boolean;
  fecha_actualizacion: string;
  equipos: EstadisticasEquipo[];
  temporadas_disponibles: TemporadaDisponible[];
  temporada_actual: string | null;
}
