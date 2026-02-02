/**
 * apuestas.ts — Servicios de API para apuestas de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type {
  ApuestaFutbol,
  ApuestaFutbolRequest,
  FiltrosApuestas,
  ResumenApuestasFutbol,
  ResumenResolucion,
  FiltrosEstadisticas,
  PartidoFutbolResumen,
  TipoMercadoFutbol,
  NivelConfianza,
  EstadoApuesta,
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
 * Transforma una apuesta de snake_case a camelCase
 */
function transformarApuesta(data: Record<string, unknown>): ApuestaFutbol {
  return {
    id: String(data.id || ''),
    partidoId: String(data.partido_id || ''),
    partido: transformarPartidoResumen((data.partido || {}) as Record<string, unknown>),
    mercado: String(data.mercado || '') as TipoMercadoFutbol,
    lado: (data.lado as 'OVER' | 'UNDER') || 'OVER',
    linea: Number(data.linea || 0),
    cuota: Number(data.cuota || 0),
    stake: Number(data.stake || 0),
    estado: (data.estado as EstadoApuesta) || 'PENDIENTE',
    // Análisis del sistema
    probabilidadSistema: Number(data.probabilidad_sistema || data.probabilidad || 0),
    confianza: (data.confianza as NivelConfianza) || 'MEDIA',
    valorEsperado: Number(data.valor_esperado || 0),
    gananciasPotenciales: Number(data.ganancias_potenciales || 0),
    // Resultado
    resultadoReal:
      data.resultado_real !== undefined ? Number(data.resultado_real) : undefined,
    gananciasReales:
      data.ganancias_reales !== undefined ? Number(data.ganancias_reales) : undefined,
    // Metadata
    casaApuestas: data.casa_apuestas as string | undefined,
    notas: data.notas as string | undefined,
    fechaCreacion: String(data.fecha_creacion || ''),
    fechaResolucion: data.fecha_resolucion as string | undefined,
  };
}

/**
 * Transforma resumen de apuestas de snake_case a camelCase
 */
function transformarResumen(data: Record<string, unknown>): ResumenApuestasFutbol {
  return {
    total: Number(data.total || 0),
    pendientes: Number(data.pendientes || 0),
    ganadas: Number(data.ganadas || 0),
    perdidas: Number(data.perdidas || 0),
    push: Number(data.push || 0),
    roi: data.roi !== null && data.roi !== undefined ? Number(data.roi) : null,
    winRate: data.win_rate !== null && data.win_rate !== undefined ? Number(data.win_rate) : null,
    stakeTotal: Number(data.stake_total || 0),
    gananciaNeta: Number(data.ganancia_neta || 0),
  };
}

// ══════════════════════════════════════════════════════════════
// SERVICIOS
// ══════════════════════════════════════════════════════════════

/**
 * Crea una nueva apuesta
 */
export async function crearApuesta(
  apuesta: ApuestaFutbolRequest
): Promise<ApuestaFutbol> {
  try {
    const body = {
      partido_id: apuesta.partidoId,
      mercado: apuesta.mercado,
      lado: apuesta.lado,
      linea: apuesta.linea,
      cuota: apuesta.cuota,
      stake: apuesta.stake,
      casa_apuestas: apuesta.casaApuestas,
      notas: apuesta.notas,
    };

    const respuesta = await clienteAPI.post('/api/futbol/apuestas', body);
    return transformarApuesta(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene la lista de apuestas con resumen
 */
export async function obtenerApuestas(filtros?: FiltrosApuestas): Promise<{
  apuestas: ApuestaFutbol[];
  resumen: ResumenApuestasFutbol;
}> {
  try {
    const params: Record<string, string | number> = {};

    if (filtros?.estado) {
      params.estado = filtros.estado;
    }
    if (filtros?.mercado) {
      params.mercado = filtros.mercado;
    }
    if (filtros?.confianza) {
      params.confianza = filtros.confianza;
    }
    if (filtros?.desde) {
      params.desde = filtros.desde;
    }
    if (filtros?.hasta) {
      params.hasta = filtros.hasta;
    }
    if (filtros?.busqueda) {
      params.busqueda = filtros.busqueda;
    }
    if (filtros?.limite) {
      params.limite = filtros.limite;
    }
    if (filtros?.offset) {
      params.offset = filtros.offset;
    }

    const respuesta = await clienteAPI.get('/api/futbol/apuestas', { params });
    const datos = respuesta.data;

    const apuestas = datos.apuestas || datos.items || [];
    const resumen = datos.resumen || {};

    return {
      apuestas: Array.isArray(apuestas)
        ? apuestas.map((a) => transformarApuesta(a as Record<string, unknown>))
        : [],
      resumen: transformarResumen(resumen),
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene una apuesta por su ID
 */
export async function obtenerApuesta(id: string): Promise<ApuestaFutbol> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/apuestas/${id}`);
    return transformarApuesta(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Actualiza una apuesta
 */
export async function actualizarApuesta(
  id: string,
  datos: Partial<ApuestaFutbolRequest>
): Promise<ApuestaFutbol> {
  try {
    const body: Record<string, unknown> = {};

    if (datos.linea !== undefined) {
      body.linea = datos.linea;
    }
    if (datos.cuota !== undefined) {
      body.cuota = datos.cuota;
    }
    if (datos.stake !== undefined) {
      body.stake = datos.stake;
    }
    if (datos.casaApuestas !== undefined) {
      body.casa_apuestas = datos.casaApuestas;
    }
    if (datos.notas !== undefined) {
      body.notas = datos.notas;
    }

    const respuesta = await clienteAPI.patch(`/api/futbol/apuestas/${id}`, body);
    return transformarApuesta(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Cancela una apuesta
 */
export async function cancelarApuesta(id: string): Promise<void> {
  try {
    await clienteAPI.delete(`/api/futbol/apuestas/${id}`);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Resuelve apuestas pendientes
 */
export async function resolverApuestas(partidoId?: string): Promise<ResumenResolucion> {
  try {
    const params: Record<string, string> = {};
    if (partidoId) {
      params.partido_id = partidoId;
    }

    const respuesta = await clienteAPI.post('/api/futbol/apuestas/resolver', null, {
      params,
    });

    return {
      procesadas: Number(respuesta.data.procesadas || 0),
      ganadas: Number(respuesta.data.ganadas || 0),
      perdidas: Number(respuesta.data.perdidas || 0),
      push: Number(respuesta.data.push || 0),
      errores: Number(respuesta.data.errores || 0),
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene estadísticas de apuestas
 */
export async function obtenerEstadisticas(
  filtros?: FiltrosEstadisticas
): Promise<ResumenApuestasFutbol> {
  try {
    const params: Record<string, string> = {};

    if (filtros?.mercado) {
      params.mercado = filtros.mercado;
    }
    if (filtros?.desde) {
      params.desde = filtros.desde;
    }
    if (filtros?.hasta) {
      params.hasta = filtros.hasta;
    }

    const respuesta = await clienteAPI.get('/api/futbol/apuestas/estadisticas', {
      params,
    });
    return transformarResumen(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
