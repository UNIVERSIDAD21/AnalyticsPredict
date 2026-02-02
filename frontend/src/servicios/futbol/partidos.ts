/**
 * partidos.ts — Servicios de API para partidos de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type {
  PartidoFutbolResumen,
  PartidoFutbolDetalle,
  FiltrosPartidos,
  EstadisticasEquipoFutbol,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TRANSFORMADORES
// ══════════════════════════════════════════════════════════════

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
    promedioGolesFavor: Number(data.promedio_goles_favor || 0),
    promedioGolesContra: Number(data.promedio_goles_contra || 0),
    promedioCornersFavor: Number(data.promedio_corners_favor || 0),
    promedioCornersContra: Number(data.promedio_corners_contra || 0),
    promedioDisparos: Number(data.promedio_disparos || 0),
    promedioGolesFavorLocal: Number(data.promedio_goles_favor_local || 0),
    promedioGolesFavorVisitante: Number(data.promedio_goles_favor_visitante || 0),
    promedioCornersFavorLocal: Number(data.promedio_corners_favor_local || 0),
    promedioCornersFavorVisitante: Number(data.promedio_corners_favor_visitante || 0),
  };
}

/**
 * Transforma un partido detalle de snake_case a camelCase
 */
function transformarPartidoDetalle(
  data: Record<string, unknown>
): PartidoFutbolDetalle {
  const resumen = transformarPartidoResumen(data);

  return {
    ...resumen,
    // Goles por tiempo
    localGoles1t: data.local_goles_1t !== undefined ? Number(data.local_goles_1t) : undefined,
    localGoles2t: data.local_goles_2t !== undefined ? Number(data.local_goles_2t) : undefined,
    localGolesTotal:
      data.local_goles_total !== undefined ? Number(data.local_goles_total) : undefined,
    visitanteGoles1t:
      data.visitante_goles_1t !== undefined ? Number(data.visitante_goles_1t) : undefined,
    visitanteGoles2t:
      data.visitante_goles_2t !== undefined ? Number(data.visitante_goles_2t) : undefined,
    visitanteGolesTotal:
      data.visitante_goles_total !== undefined ? Number(data.visitante_goles_total) : undefined,
    // Corners por tiempo
    localCorners1t:
      data.local_corners_1t !== undefined ? Number(data.local_corners_1t) : undefined,
    localCorners2t:
      data.local_corners_2t !== undefined ? Number(data.local_corners_2t) : undefined,
    localCornersTotal:
      data.local_corners_total !== undefined ? Number(data.local_corners_total) : undefined,
    visitanteCorners1t:
      data.visitante_corners_1t !== undefined ? Number(data.visitante_corners_1t) : undefined,
    visitanteCorners2t:
      data.visitante_corners_2t !== undefined ? Number(data.visitante_corners_2t) : undefined,
    visitanteCornersTotal:
      data.visitante_corners_total !== undefined
        ? Number(data.visitante_corners_total)
        : undefined,
    // Disparos
    localDisparosTotal:
      data.local_disparos_total !== undefined ? Number(data.local_disparos_total) : undefined,
    localDisparosArco:
      data.local_disparos_arco !== undefined ? Number(data.local_disparos_arco) : undefined,
    visitanteDisparosTotal:
      data.visitante_disparos_total !== undefined
        ? Number(data.visitante_disparos_total)
        : undefined,
    visitanteDisparosArco:
      data.visitante_disparos_arco !== undefined
        ? Number(data.visitante_disparos_arco)
        : undefined,
    // Estadísticas de equipos
    estadisticasLocal: data.estadisticas_local
      ? transformarEstadisticas(data.estadisticas_local as Record<string, unknown>)
      : undefined,
    estadisticasVisitante: data.estadisticas_visitante
      ? transformarEstadisticas(data.estadisticas_visitante as Record<string, unknown>)
      : undefined,
  };
}

// ══════════════════════════════════════════════════════════════
// SERVICIOS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene los partidos próximos
 */
export async function obtenerPartidosProximos(
  filtros?: FiltrosPartidos
): Promise<PartidoFutbolResumen[]> {
  try {
    const params: Record<string, string | number> = {};

    if (filtros?.competicion) {
      params.competicion = filtros.competicion;
    }
    if (filtros?.dias) {
      params.dias = filtros.dias;
    }
    if (filtros?.equipo) {
      params.equipo = filtros.equipo;
    }
    if (filtros?.limite) {
      params.limite = filtros.limite;
    }

    const respuesta = await clienteAPI.get('/api/futbol/partidos/proximos', {
      params,
    });
    const datos = respuesta.data?.partidos || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarPartidoResumen) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene los partidos recientes (finalizados)
 */
export async function obtenerPartidosRecientes(
  filtros?: FiltrosPartidos
): Promise<PartidoFutbolResumen[]> {
  try {
    const params: Record<string, string | number> = {};

    if (filtros?.competicion) {
      params.competicion = filtros.competicion;
    }
    if (filtros?.dias) {
      params.dias = filtros.dias;
    }
    if (filtros?.equipo) {
      params.equipo = filtros.equipo;
    }
    if (filtros?.limite) {
      params.limite = filtros.limite;
    }

    const respuesta = await clienteAPI.get('/api/futbol/partidos/recientes', {
      params,
    });
    const datos = respuesta.data?.partidos || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarPartidoResumen) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene el detalle de un partido
 */
export async function obtenerPartido(id: string): Promise<PartidoFutbolDetalle> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/partidos/${id}`);
    return transformarPartidoDetalle(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
