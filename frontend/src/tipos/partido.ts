/**
 * partido.ts — Tipos relacionados con partidos
 *
 * Estos tipos son CRÍTICOS para que el formulario de análisis
 * pueda enviar partido_id y así el sistema registre predicciones.
 */

// ══════════════════════════════════════════════════════════════
// TIPOS DE PARTIDO
// ══════════════════════════════════════════════════════════════

/**
 * Resumen de un partido para selección en UI
 */
export interface PartidoResumen {
  /** UUID del partido */
  id: string;
  /** Fecha del partido (YYYY-MM-DD) */
  fecha_partido: string;
  /** Tipo: PRE, REG, POST */
  tipo_partido: string;
  /** UUID del equipo local */
  equipo_local_id: string;
  /** Nombre del equipo local */
  equipo_local_nombre: string;
  /** UUID del equipo visitante */
  equipo_visitante_id: string;
  /** Nombre del equipo visitante */
  equipo_visitante_nombre: string;
  /** UUID de la temporada */
  temporada_id: string;
  /** Nombre de la temporada */
  temporada_nombre: string;
  /** Puntos del local (null si no ha terminado) */
  local_total: number | null;
  /** Puntos del visitante (null si no ha terminado) */
  visitante_total: number | null;
  /** Si el partido ya terminó */
  finalizado: boolean;
}

/**
 * Respuesta de la API de partidos
 */
export interface RespuestaPartidos {
  exito: boolean;
  partidos: PartidoResumen[];
  total: number;
  mensaje?: string;
}

/**
 * Parámetros para buscar partidos
 */
export interface ParametrosBusquedaPartidos {
  fecha_desde?: string;
  fecha_hasta?: string;
  equipo_id?: string;
  solo_futuros?: boolean;
  solo_finalizados?: boolean;
  limite?: number;
}

/**
 * Partido seleccionado para análisis
 * Contiene todos los campos necesarios para el registro de predicciones
 */
export interface PartidoSeleccionado {
  partido_id: string;
  temporada_id: string;
  equipo_local_id: string;
  equipo_local_nombre: string;
  equipo_visitante_id: string;
  equipo_visitante_nombre: string;
  fecha_partido: string;
  tipo_partido: string;
}
