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
 * Compara dos fechas por año, mes y día (ignora hora/minutos/segundos)
 */
function sonMismaFecha(fecha1: Date, fecha2: Date): boolean {
  return (
    fecha1.getFullYear() === fecha2.getFullYear() &&
    fecha1.getMonth() === fecha2.getMonth() &&
    fecha1.getDate() === fecha2.getDate()
  );
}

/**
 * Formatea fecha para mostrar en UI
 * Usa comparación por año/mes/día para evitar problemas de timezone
 */
export function formatearFechaPartido(fecha: string): string {
  const date = parsearFechaPartido(fecha);
  const hoy = obtenerFechaNBAHoy();

  const manana = new Date(hoy);
  manana.setDate(manana.getDate() + 1);
  const ayer = new Date(hoy);
  ayer.setDate(ayer.getDate() - 1);

  // Comparar por año/mes/día en lugar de getTime() para evitar problemas de timezone
  if (sonMismaFecha(date, hoy)) {
    return 'Hoy';
  }
  if (sonMismaFecha(date, manana)) {
    return 'Mañana';
  }
  if (sonMismaFecha(date, ayer)) {
    return 'Ayer';
  }

  return date.toLocaleDateString('es-CO', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}

/**
 * Obtiene la fecha actual como string YYYY-MM-DD (Eastern Time)
 */
export function obtenerFechaNBAHoyString(): string {
  const fecha = obtenerFechaNBAHoy();
  const year = fecha.getFullYear();
  const month = String(fecha.getMonth() + 1).padStart(2, '0');
  const day = String(fecha.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
