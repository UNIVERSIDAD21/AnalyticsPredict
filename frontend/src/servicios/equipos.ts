/**
 * equipos.ts — Servicio para operaciones con equipos
 */

import { clienteAPI, extraerMensajeError } from './api';
import {
  Equipo,
  RespuestaEquipos,
  OpcionEquipo,
  RespuestaHistorialEquipo,
  RespuestaTemporadasEquipos,
  TemporadaDisponible,
} from '../tipos';

// ══════════════════════════════════════════════════════════════
// FUNCIONES
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene la lista de todos los equipos NBA
 */
export async function obtenerEquipos(): Promise<Equipo[]> {
  try {
    const respuesta = await clienteAPI.get<RespuestaEquipos>('/api/equipos');

    if (!respuesta.data.exito) {
      throw new Error('Error al obtener equipos');
    }

    return respuesta.data.equipos;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

interface ParametrosHistorialEquipo {
  temporadaId?: string;
  comoLocal?: boolean;
  orden?: 'asc' | 'desc';
}

/**
 * Obtiene el historial completo de partidos de un equipo
 */
export async function obtenerHistorialEquipo(
  equipoId: string,
  parametros: ParametrosHistorialEquipo
): Promise<RespuestaHistorialEquipo> {
  try {
    const respuesta = await clienteAPI.get<RespuestaHistorialEquipo>(
      `/api/equipos/${equipoId}/partidos`,
      {
        params: {
          temporada_id: parametros.temporadaId,
          como_local: parametros.comoLocal,
          orden: parametros.orden,
        },
      }
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al obtener historial del equipo');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene las temporadas disponibles para uno o más equipos
 */
export async function obtenerTemporadasEquipos(
  equipoIds: string[]
): Promise<TemporadaDisponible[]> {
  try {
    const respuesta = await clienteAPI.get<RespuestaTemporadasEquipos>(
      '/api/equipos/temporadas',
      {
        params: {
          equipo_ids: equipoIds,
        },
      }
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al obtener temporadas disponibles');
    }

    return respuesta.data.temporadas || [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Convierte la lista de equipos a opciones para selector
 */
export function equiposAOpciones(equipos: Equipo[]): OpcionEquipo[] {
  return equipos.map((equipo) => ({
    valor: equipo.nombre.toLowerCase(),
    etiqueta: `${equipo.nombre} (${equipo.abreviatura})`,
    equipo,
  }));
}

/**
 * Busca un equipo por su nombre normalizado
 */
export function buscarEquipo(equipos: Equipo[], nombre: string): Equipo | undefined {
  const nombreNormalizado = nombre.toLowerCase().trim();
  return equipos.find(
    (equipo) =>
      equipo.nombre.toLowerCase() === nombreNormalizado ||
      equipo.nombre_corto.toLowerCase() === nombreNormalizado ||
      equipo.abreviatura.toLowerCase() === nombreNormalizado
  );
}

/**
 * Filtra equipos por texto de búsqueda
 */
export function filtrarEquipos(equipos: Equipo[], busqueda: string): Equipo[] {
  if (!busqueda.trim()) {
    return equipos;
  }

  const termino = busqueda.toLowerCase().trim();

  return equipos.filter(
    (equipo) =>
      equipo.nombre.toLowerCase().includes(termino) ||
      equipo.nombre_corto.toLowerCase().includes(termino) ||
      equipo.abreviatura.toLowerCase().includes(termino)
  );
}
