/**
 * api.ts — Tipos para comunicación con el backend
 */

/**
 * Error estándar de la API
 */
export interface ErrorAPI {
  exito: false;
  error: {
    tipo: string;
    mensaje: string;
    equipo?: string;
    campo?: string;
    detalle?: string;
  };
  sugerencia?: string;
}

/**
 * Estado de una petición
 */
export type EstadoPeticion = 'inactivo' | 'cargando' | 'exito' | 'error';

/**
 * Resultado genérico de una petición
 */
export interface ResultadoPeticion<T> {
  estado: EstadoPeticion;
  datos: T | null;
  error: string | null;
}
