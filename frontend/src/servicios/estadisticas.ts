/**
 * estadisticas.ts — Servicio para estadísticas de equipos
 */

import { clienteAPI, extraerMensajeError } from './api';
import { EstadisticasEquipo, RespuestaEstadisticasEquipos } from '../tipos';

/**
 * Obtiene estadísticas agregadas de equipos
 */
export async function obtenerEstadisticasEquipos(): Promise<RespuestaEstadisticasEquipos> {
  try {
    const respuesta = await clienteAPI.get<RespuestaEstadisticasEquipos>('/api/estadisticas-equipos');

    if (!respuesta.data.exito) {
      throw new Error('Error al obtener estadísticas de equipos');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Busca estadísticas por nombre de equipo
 */
export function buscarEstadisticasEquipo(
  equipos: EstadisticasEquipo[],
  nombre: string
): EstadisticasEquipo | undefined {
  const termino = nombre.toLowerCase().trim();
  return equipos.find(
    (equipo) =>
      equipo.nombre.toLowerCase() === termino ||
      equipo.abreviatura.toLowerCase() === termino
  );
}
