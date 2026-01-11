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
 * Obtiene la fecha actual según el calendario NBA (Eastern Time) como string YYYY-MM-DD.
 * Esta función es la fuente de verdad para "qué día es hoy" en el contexto NBA.
 */
export function obtenerFechaNBAHoyString(): string {
  const ahora = new Date();
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });

  const partes = formatter.formatToParts(ahora);
  const year = partes.find((p) => p.type === 'year')?.value || '1970';
  const month = partes.find((p) => p.type === 'month')?.value || '01';
  const day = partes.find((p) => p.type === 'day')?.value || '01';

  return `${year}-${month}-${day}`;
}

/**
 * Obtiene la fecha actual según el calendario NBA (Eastern Time).
 * @deprecated Usar obtenerFechaNBAHoyString() para evitar problemas de timezone.
 */
export function obtenerFechaNBAHoy(): Date {
  const fechaStr = obtenerFechaNBAHoyString();
  return parsearFechaPartido(fechaStr);
}

/**
 * Parsea una fecha YYYY-MM-DD evitando el desfase de timezone.
 */
export function parsearFechaPartido(fechaStr: string): Date {
  const [year, month, day] = fechaStr.split('-').map(Number);
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
 * Calcula una fecha relativa a partir de una fecha base (como string YYYY-MM-DD).
 */
function calcularFechaRelativa(fechaBase: string, dias: number): string {
  const [year, month, day] = fechaBase.split('-').map(Number);
  const fecha = new Date(year, month - 1, day);
  fecha.setDate(fecha.getDate() + dias);

  const y = fecha.getFullYear();
  const m = String(fecha.getMonth() + 1).padStart(2, '0');
  const d = String(fecha.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/**
 * Formatea fecha para mostrar en UI.
 * Compara fechas como strings para evitar problemas de timezone.
 */
export function formatearFechaPartido(fecha: string): string {
  // Normalizar la fecha de entrada a formato YYYY-MM-DD
  const fechaNormalizada = fecha.includes('T') ? fecha.split('T')[0] : fecha;

  // Obtener la fecha de hoy en ET como string
  const hoyStr = obtenerFechaNBAHoyString();
  const mananaStr = calcularFechaRelativa(hoyStr, 1);
  const ayerStr = calcularFechaRelativa(hoyStr, -1);

  // Comparar directamente como strings (formato YYYY-MM-DD es ordenable)
  if (fechaNormalizada === hoyStr) {
    return 'Hoy';
  }
  if (fechaNormalizada === mananaStr) {
    return 'Mañana';
  }
  if (fechaNormalizada === ayerStr) {
    return 'Ayer';
  }

  // Para otras fechas, parsear y formatear
  const date = parsearFechaPartido(fechaNormalizada);
  return date.toLocaleDateString('es-CO', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}
