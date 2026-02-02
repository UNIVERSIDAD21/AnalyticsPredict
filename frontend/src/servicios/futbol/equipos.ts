/**
 * equipos.ts — Servicios de API para equipos de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type {
  EquipoFutbol,
  EstadisticasEquipoFutbol,
  PartidoFutbolResumen,
  PartidoFutbolEstadistico,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TRANSFORMADORES
// ══════════════════════════════════════════════════════════════

/**
 * Transforma un equipo de snake_case a camelCase
 */
function transformarEquipo(data: Record<string, unknown>): EquipoFutbol {
  return {
    id: String(data.id || ''),
    nombre: String(data.nombre || ''),
    nombreCorto: String(data.nombre_corto || data.nombre || ''),
    pais: String(data.pais || ''),
    competicionPrincipal: String(data.competicion_principal || ''),
    logoUrl: data.logo_url as string | undefined,
  };
}

/**
 * Transforma estadísticas de equipo de snake_case a camelCase
 */
function transformarEstadisticas(
  data: Record<string, unknown>
): EstadisticasEquipoFutbol {
  return {
    partidosJugados: Number(data.partidos_jugados || 0),
    victorias: Number(data.victorias || 0),
    empates: Number(data.empates || 0),
    derrotas: Number(data.derrotas || 0),
    golesFavor: Number(data.goles_favor || 0),
    golesContra: Number(data.goles_contra || 0),
    cornersFavor: Number(data.corners_favor || 0),
    cornersContra: Number(data.corners_contra || 0),
    disparosTotal: Number(data.disparos_total || 0),
    disparosArco: Number(data.disparos_arco || 0),
    // Promedios
    promedioGolesFavor: Number(data.promedio_goles_favor || 0),
    promedioGolesContra: Number(data.promedio_goles_contra || 0),
    promedioCornersFavor: Number(data.promedio_corners_favor || 0),
    promedioCornersContra: Number(data.promedio_corners_contra || 0),
    promedioDisparos: Number(data.promedio_disparos || 0),
    // Por ubicación
    promedioGolesFavorLocal: Number(data.promedio_goles_favor_local || 0),
    promedioGolesFavorVisitante: Number(data.promedio_goles_favor_visitante || 0),
    promedioCornersFavorLocal: Number(data.promedio_corners_favor_local || 0),
    promedioCornersFavorVisitante: Number(data.promedio_corners_favor_visitante || 0),
  };
}

/**
 * Transforma un partido resumen de snake_case a camelCase
 */
function transformarPartidoResumen(
  data: Record<string, unknown>
): PartidoFutbolResumen {
  return {
    id: String(data.id || ''),
    competicion: String(data.competicion || ''),
    competicionNombre: String(data.competicion_nombre || ''),
    fechaPartido: String(data.fecha_partido || ''),
    equipoLocal: String(data.equipo_local || ''),
    equipoLocalNombre: String(data.equipo_local_nombre || ''),
    equipoLocalLogo: data.equipo_local_logo as string | undefined,
    equipoVisitante: String(data.equipo_visitante || ''),
    equipoVisitanteNombre: String(data.equipo_visitante_nombre || ''),
    equipoVisitanteLogo: data.equipo_visitante_logo as string | undefined,
    estado: (data.estado as PartidoFutbolResumen['estado']) || 'PROGRAMADO',
    jornada: data.jornada ? Number(data.jornada) : undefined,
    golesLocal: data.goles_local !== undefined ? Number(data.goles_local) : undefined,
    golesVisitante:
      data.goles_visitante !== undefined ? Number(data.goles_visitante) : undefined,
  };
}

/**
 * Transforma un partido estadístico de snake_case a camelCase
 */
function transformarPartidoEstadistico(
  data: Record<string, unknown>
): PartidoFutbolEstadistico {
  return {
    id: String(data.id || ''),
    fechaPartido: String(data.fecha_partido || ''),
    equipoLocalId: String(data.equipo_local_id || ''),
    equipoVisitanteId: String(data.equipo_visitante_id || ''),
    equipoLocalNombre: String(data.equipo_local || ''),
    equipoVisitanteNombre: String(data.equipo_visitante || ''),
    golesLocal: Number(data.goles_local ?? data.local_goles_total ?? 0),
    golesVisitante: Number(data.goles_visitante ?? data.visitante_goles_total ?? 0),
    cornersLocal: Number(data.corners_local ?? data.local_corners_total ?? 0),
    cornersVisitante: Number(data.corners_visitante ?? data.visitante_corners_total ?? 0),
    disparosLocal: Number(data.disparos_local ?? data.local_disparos_total ?? 0),
    disparosVisitante: Number(data.disparos_visitante ?? data.visitante_disparos_total ?? 0),
    disparosArcoLocal: Number(data.disparos_arco_local ?? data.local_disparos_arco ?? 0),
    disparosArcoVisitante: Number(
      data.disparos_arco_visitante ?? data.visitante_disparos_arco ?? 0
    ),
  };
}

// ══════════════════════════════════════════════════════════════
// SERVICIOS
// ══════════════════════════════════════════════════════════════

/**
 * Busca equipos por nombre
 */
export async function buscarEquipos(busqueda: string): Promise<EquipoFutbol[]> {
  try {
    const respuesta = await clienteAPI.get('/api/futbol/equipos', {
      params: { busqueda },
    });
    const datos = respuesta.data?.equipos || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarEquipo) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene un equipo por su ID
 */
export async function obtenerEquipo(id: string): Promise<EquipoFutbol> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/equipos/${id}`);
    return transformarEquipo(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene las estadísticas de un equipo
 */
export async function obtenerEstadisticasEquipo(
  id: string,
  temporada?: string
): Promise<EstadisticasEquipoFutbol> {
  try {
    const params: Record<string, string> = {};
    if (temporada) {
      params.temporada = temporada;
    }

    const respuesta = await clienteAPI.get(`/api/futbol/equipos/${id}/estadisticas`, {
      params,
    });
    return transformarEstadisticas(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene los partidos recientes de un equipo
 */
export async function obtenerPartidosEquipo(
  id: string,
  limite: number = 10
): Promise<PartidoFutbolResumen[]> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/equipos/${id}/partidos`, {
      params: { limite },
    });
    const datos = respuesta.data?.partidos || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarPartidoResumen) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene los partidos recientes de un equipo con estadísticas
 */
export async function obtenerPartidosEquipoDetalle(
  id: string,
  limite: number = 10
): Promise<PartidoFutbolEstadistico[]> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/equipos/${id}/partidos-detalle`, {
      params: { limite },
    });
    const datos = respuesta.data?.partidos || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarPartidoEstadistico) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
