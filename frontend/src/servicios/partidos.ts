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
 * Obtiene la fecha actual según el calendario NBA (Eastern Time).
 */
export function obtenerFechaNBAHoy(): Date {
  const ahora = new Date();
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });

  const partes = formatter.formatToParts(ahora);
  const year = parseInt(partes.find((p) => p.type === 'year')?.value || '1970', 10);
  const month = parseInt(partes.find((p) => p.type === 'month')?.value || '01', 10) - 1;
  const day = parseInt(partes.find((p) => p.type === 'day')?.value || '01', 10);

  const fechaHoy = new Date(year, month, day);
  fechaHoy.setHours(0, 0, 0, 0);
  return fechaHoy;
}

/**
 * Obtiene la fecha actual del calendario NBA en formato ISO (YYYY-MM-DD).
 */
export function obtenerFechaHoyISO(): string {
  const fecha = obtenerFechaNBAHoy();
  const year = fecha.getFullYear();
  const month = `${fecha.getMonth() + 1}`.padStart(2, '0');
  const day = `${fecha.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Normaliza una fecha ISO (YYYY-MM-DD o YYYY-MM-DDTHH:mm:ss) a YYYY-MM-DD.
 */
export function normalizarFechaISO(fechaStr: string): string {
  if (!fechaStr) {
    return '';
  }
  const [soloFecha] = fechaStr.split('T');
  return soloFecha;
}

/**
 * Parsea una fecha YYYY-MM-DD evitando el desfase de timezone.
 */
export function parsearFechaPartido(fechaStr: string): Date {
  const normalizada = normalizarFechaISO(fechaStr);
  const [year, month, day] = normalizada.split('-').map(Number);
  const fecha = new Date(year, month - 1, day);
  fecha.setHours(0, 0, 0, 0);
  return fecha;
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
  const date = parsearFechaPartido(fecha);
  const hoy = obtenerFechaNBAHoy();

  const manana = new Date(hoy);
  manana.setDate(manana.getDate() + 1);
  const ayer = new Date(hoy);
  ayer.setDate(ayer.getDate() - 1);

  if (date.getTime() === hoy.getTime()) {
    return 'Hoy';
  }
  if (date.getTime() === manana.getTime()) {
    return 'Mañana';
  }
  if (date.getTime() === ayer.getTime()) {
    return 'Ayer';
  }

  return date.toLocaleDateString('es-CO', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}
