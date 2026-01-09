/**
 * partidos.ts — Servicio para consultar partidos
 *
 * CRÍTICO para que el formulario de análisis pueda:
 * 1. Mostrar partidos disponibles para selección
 * 2. Enviar partido_id al backend para registro de predicciones
 *
 * Sin esto, las predicciones NO se registran y la calibración está muerta.
 */

import { clienteAPI, extraerMensajeError } from './api';
import {
  PartidoResumen,
  RespuestaPartidos,
  ParametrosBusquedaPartidos,
} from '../tipos';

// ══════════════════════════════════════════════════════════════
// FUNCIONES DE CONSULTA
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene partidos con filtros opcionales
 */
export async function obtenerPartidos(
  params?: ParametrosBusquedaPartidos
): Promise<PartidoResumen[]> {
  try {
    const respuesta = await clienteAPI.get<RespuestaPartidos>('/api/partidos', {
      params,
    });

    if (!respuesta.data.exito) {
      throw new Error(respuesta.data.mensaje || 'Error obteniendo partidos');
    }

    return respuesta.data.partidos;
  } catch (error) {
    console.error('Error obteniendo partidos:', extraerMensajeError(error));
    throw error;
  }
}

/**
 * Obtiene partidos del día actual
 */
export async function obtenerPartidosHoy(): Promise<PartidoResumen[]> {
  try {
    const respuesta = await clienteAPI.get<RespuestaPartidos>('/api/partidos/hoy');

    if (!respuesta.data.exito) {
      throw new Error(respuesta.data.mensaje || 'Error obteniendo partidos de hoy');
    }

    return respuesta.data.partidos;
  } catch (error) {
    console.error('Error obteniendo partidos de hoy:', extraerMensajeError(error));
    throw error;
  }
}

/**
 * Obtiene partidos próximos (futuros sin resultado)
 */
export async function obtenerPartidosProximos(
  dias: number = 7
): Promise<PartidoResumen[]> {
  try {
    const diasNormalizados = Number.isFinite(dias) ? Math.min(Math.max(dias, 1), 30) : 7;
    const respuesta = await clienteAPI.get<RespuestaPartidos>('/api/partidos/proximos', {
      params: { dias: diasNormalizados },
    });

    if (!respuesta.data.exito) {
      throw new Error(respuesta.data.mensaje || 'Error obteniendo partidos próximos');
    }

    return respuesta.data.partidos;
  } catch (error) {
    console.error('Error obteniendo partidos próximos:', extraerMensajeError(error));
    throw error;
  }
}

/**
 * Busca partido por nombres de equipos y fecha opcional
 */
export async function buscarPartido(
  equipoLocal: string,
  equipoVisitante: string,
  fecha?: string
): Promise<PartidoResumen[]> {
  try {
    const respuesta = await clienteAPI.get<RespuestaPartidos>('/api/partidos/buscar', {
      params: {
        equipo_local: equipoLocal,
        equipo_visitante: equipoVisitante,
        fecha,
      },
    });

    if (!respuesta.data.exito) {
      throw new Error(respuesta.data.mensaje || 'Error buscando partido');
    }

    return respuesta.data.partidos;
  } catch (error) {
    console.error('Error buscando partido:', extraerMensajeError(error));
    throw error;
  }
}

/**
 * Agrupa partidos por fecha para mostrar en calendario
 */
export function agruparPartidosPorFecha(
  partidos: PartidoResumen[]
): Map<string, PartidoResumen[]> {
  const agrupados = new Map<string, PartidoResumen[]>();

  for (const partido of partidos) {
    const fecha = partido.fecha_partido;
    if (!agrupados.has(fecha)) {
      agrupados.set(fecha, []);
    }
    agrupados.get(fecha)!.push(partido);
  }

  return agrupados;
}

/**
 * Formatea fecha para mostrar en UI
 */
export function formatearFechaPartido(fecha: string): string {
  const date = new Date(fecha + 'T00:00:00');
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);

  const manana = new Date(hoy);
  manana.setDate(manana.getDate() + 1);

  if (date.getTime() === hoy.getTime()) {
    return 'Hoy';
  }
  if (date.getTime() === manana.getTime()) {
    return 'Mañana';
  }

  return date.toLocaleDateString('es-ES', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}
