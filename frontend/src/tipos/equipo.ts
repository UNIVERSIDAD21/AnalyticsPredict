/**
 * equipo.ts — Tipos relacionados con equipos NBA
 */

/**
 * Información básica de un equipo NBA
 */
export interface Equipo {
  id: string;
  nombre: string;
  nombre_corto: string;
  abreviatura: string;
  conferencia?: string;
  division?: string;
  /** Soporte del predictor de la liga, cuando el catálogo lo informa. */
  elegible?: boolean;
  muestras?: number;
}

/**
 * Respuesta del endpoint GET /api/equipos
 */
export interface RespuestaEquipos {
  exito: boolean;
  total: number;
  equipos: Equipo[];
}

/**
 * Opciones para el selector de equipos
 */
export interface OpcionEquipo {
  valor: string;
  etiqueta: string;
  equipo: Equipo;
}
