/**
 * partidos.ts — Servicios de API para partidos de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type {
  PartidoFutbolResumen,
  PartidoFutbolDetalle,
  FiltrosPartidos,
  EstadisticasEquipoFutbol,
  PartidoFutbolEstadistico,
} from '../../tipos/futbol';

const obtenerFechaLocalISO = (): string => {
  const ahora = new Date();
  const year = ahora.getFullYear();
  const month = String(ahora.getMonth() + 1).padStart(2, '0');
  const day = String(ahora.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

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
    temporadaId: data.temporada_id == null ? undefined : String(data.temporada_id),
    competicion: String(data.competicion_id || data.competicion || ''),
    competicionNombre: String(data.competicion_nombre || data.competicion || ''),
    fechaPartido: String(data.fecha_partido || ''),
    equipoLocal: String(data.equipo_local_id || data.equipo_local || ''),
    equipoLocalNombre: String(data.equipo_local_nombre || data.equipo_local || ''),
    equipoLocalLogo: data.equipo_local_logo as string | undefined,
    equipoVisitante: String(data.equipo_visitante_id || data.equipo_visitante || ''),
    equipoVisitanteNombre: String(data.equipo_visitante_nombre || data.equipo_visitante || ''),
    equipoVisitanteLogo: data.equipo_visitante_logo as string | undefined,
    estado: (data.estado as PartidoFutbolResumen['estado']) || 'PROGRAMADO',
    jornada: data.jornada ? Number(data.jornada) : undefined,
    golesLocal: data.goles_local != null ? Number(data.goles_local) : undefined,
    golesVisitante:
      data.goles_visitante != null ? Number(data.goles_visitante) : undefined,
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
    equipoLocalId: data.equipo_local_id ? String(data.equipo_local_id) : undefined,
    equipoVisitanteId: data.equipo_visitante_id ? String(data.equipo_visitante_id) : undefined,
    // Goles por tiempo
    localGoles1t: data.local_goles_1t != null ? Number(data.local_goles_1t) : undefined,
    localGoles2t: data.local_goles_2t != null ? Number(data.local_goles_2t) : undefined,
    localGolesTotal:
      data.local_goles_total != null ? Number(data.local_goles_total) : undefined,
    visitanteGoles1t:
      data.visitante_goles_1t != null ? Number(data.visitante_goles_1t) : undefined,
    visitanteGoles2t:
      data.visitante_goles_2t != null ? Number(data.visitante_goles_2t) : undefined,
    visitanteGolesTotal:
      data.visitante_goles_total != null ? Number(data.visitante_goles_total) : undefined,
    // Corners por tiempo
    localCorners1t:
      data.local_corners_1t != null ? Number(data.local_corners_1t) : undefined,
    localCorners2t:
      data.local_corners_2t != null ? Number(data.local_corners_2t) : undefined,
    localCornersTotal:
      data.local_corners_total != null ? Number(data.local_corners_total) : undefined,
    visitanteCorners1t:
      data.visitante_corners_1t != null ? Number(data.visitante_corners_1t) : undefined,
    visitanteCorners2t:
      data.visitante_corners_2t != null ? Number(data.visitante_corners_2t) : undefined,
    visitanteCornersTotal:
      data.visitante_corners_total != null
        ? Number(data.visitante_corners_total)
        : undefined,
    // Disparos
    localDisparosTotal:
      data.local_disparos_total != null ? Number(data.local_disparos_total) : undefined,
    localDisparosArco:
      data.local_disparos_arco != null ? Number(data.local_disparos_arco) : undefined,
    visitanteDisparosTotal:
      data.visitante_disparos_total != null
        ? Number(data.visitante_disparos_total)
        : undefined,
    visitanteDisparosArco:
      data.visitante_disparos_arco != null
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

/**
 * Transforma un partido estadístico de snake_case a camelCase
 */
export function transformarPartidoEstadistico(
  data: Record<string, unknown>
): PartidoFutbolEstadistico {
  const leer = (...campos: string[]): number | null => {
    const v = campos.map(c => data[c]).find(v => v !== null && v !== undefined);
    return typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : null;
  };
  return {
    id: String(data.id || ''),
    fechaPartido: String(data.fecha_partido || ''),
    equipoLocalId: String(data.equipo_local_id || ''),
    equipoVisitanteId: String(data.equipo_visitante_id || ''),
    equipoLocalNombre: String(data.equipo_local || ''),
    equipoVisitanteNombre: String(data.equipo_visitante || ''),
    golesLocal: leer('goles_local', 'local_goles_total'),
    golesLocal1t: leer('goles_local_1t', 'local_goles_1t'),
    golesLocal2t: leer('goles_local_2t', 'local_goles_2t'),
    golesVisitante1t: leer('goles_visitante_1t', 'visitante_goles_1t'),
    golesVisitante2t: leer('goles_visitante_2t', 'visitante_goles_2t'),
    golesVisitante: leer('goles_visitante', 'visitante_goles_total'),
    cornersLocal: leer('corners_local', 'local_corners_total'),
    cornersVisitante: leer('corners_visitante', 'visitante_corners_total'),
    cornersLocal1t: leer('corners_local_1t', 'local_corners_1t'),
    cornersLocal2t: leer('corners_local_2t', 'local_corners_2t'),
    cornersVisitante1t: leer('corners_visitante_1t', 'visitante_corners_1t'),
    cornersVisitante2t: leer('corners_visitante_2t', 'visitante_corners_2t'),
    disparosLocal: leer('disparos_local', 'local_disparos_total'),
    disparosVisitante: leer('disparos_visitante', 'visitante_disparos_total'),
    disparosArcoLocal: leer('disparos_arco_local', 'local_disparos_arco'),
    disparosArcoVisitante: leer('disparos_arco_visitante', 'visitante_disparos_arco'),
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
      params.competicion_id = filtros.competicion;
    }
    if (filtros?.dias) {
      params.dias = filtros.dias;
    }
    if (filtros?.equipo) {
      params.equipo_id = filtros.equipo;
    }
    if (filtros?.limite) {
      params.tamano = filtros.limite;
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
      params.competicion_id = filtros.competicion;
    }
    if (filtros?.dias) {
      params.dias = filtros.dias;
    }
    if (filtros?.equipo) {
      params.equipo_id = filtros.equipo;
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
 * Obtiene los partidos de hoy (programados, en curso y finalizados)
 */
export async function obtenerPartidosHoy(
  filtros?: FiltrosPartidos
): Promise<PartidoFutbolResumen[]> {
  try {
    const params: Record<string, string | number> = {};
    params.fecha = obtenerFechaLocalISO();

    if (filtros?.competicion) {
      params.competicion_id = filtros.competicion;
    }
    if (filtros?.equipo) {
      params.equipo_id = filtros.equipo;
    }

    const respuesta = await clienteAPI.get('/api/futbol/partidos/hoy', {
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
export async function obtenerPartido(id: string, incluirEstadisticas = true): Promise<PartidoFutbolDetalle> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/partidos/${id}`, { params: { incluir_estadisticas: incluirEstadisticas } });
    return transformarPartidoDetalle(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene enfrentamientos directos entre dos equipos
 */
export async function obtenerH2HPartidos(
  equipoLocalId: string,
  equipoVisitanteId: string,
  limite?: number,
  ambito?: { competicionId: string; antesDe: string }
): Promise<PartidoFutbolEstadistico[]> {
  try {
    const params: Record<string, string | number> = {
      equipo_local_id: equipoLocalId,
      equipo_visitante_id: equipoVisitanteId,
    };
    if (limite && limite > 0) {
      params.limite = limite;
    }
    if (ambito) { params.competicion_id = ambito.competicionId; params.antes_de = ambito.antesDe; }
    const respuesta = await clienteAPI.get('/api/futbol/partidos/h2h', {
      params,
    });
    const datos = respuesta.data?.partidos || respuesta.data || [];
    return Array.isArray(datos) ? datos.map(transformarPartidoEstadistico) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
