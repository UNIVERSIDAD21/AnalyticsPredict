/**
 * competiciones.ts — Servicios de API para competiciones de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type { Competicion, FiltrosCompeticion, EquipoFutbol } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TRANSFORMADORES
// ══════════════════════════════════════════════════════════════

/**
 * Transforma una competición de snake_case a camelCase
 */
function transformarCompeticion(data: Record<string, unknown>): Competicion {
  return {
    id: String(data.id || ''),
    codigo: String(data.codigo || ''),
    nombre: String(data.nombre || ''),
    pais: String(data.pais || ''),
    tipo: (data.tipo as Competicion['tipo']) || 'liga',
    prioridad: Number(data.prioridad || 0),
    activa: Boolean(data.activa),
    logoUrl: data.logo_url as string | undefined,
  };
}

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

// ══════════════════════════════════════════════════════════════
// SERVICIOS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene la lista de competiciones disponibles
 */
export async function obtenerCompeticiones(
  filtros?: FiltrosCompeticion
): Promise<Competicion[]> {
  try {
    const params: Record<string, string> = {};

    if (filtros?.pais) {
      params.pais = filtros.pais;
    }
    if (filtros?.tipo) {
      params.tipo = filtros.tipo;
    }
    if (filtros?.activa !== undefined) {
      params.activa = String(filtros.activa);
    }

    const respuesta = await clienteAPI.get('/api/futbol/competiciones', { params });
    const datos = respuesta.data?.competiciones || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarCompeticion) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene una competición por su ID
 */
export async function obtenerCompeticion(id: string): Promise<Competicion> {
  try {
    const respuesta = await clienteAPI.get(`/api/futbol/competiciones/${id}`);
    return transformarCompeticion(respuesta.data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene los equipos de una competición
 */
export async function obtenerEquiposCompeticion(
  competicionId: string
): Promise<EquipoFutbol[]> {
  try {
    const respuesta = await clienteAPI.get(
      `/api/futbol/competiciones/${competicionId}/equipos`
    );
    const datos = respuesta.data?.equipos || respuesta.data || [];

    return Array.isArray(datos) ? datos.map(transformarEquipo) : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
