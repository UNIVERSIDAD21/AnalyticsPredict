/**
 * bitacora.ts — Servicios para la bitácora de apuestas
 */

import { clienteAPI } from './api';
import {
  PeticionActualizarResultado,
  PeticionCrearApuesta,
  RespuestaApuesta,
  RespuestaListaApuestas,
  RespuestaResumenApuestas,
} from '../tipos';

export async function crearApuesta(payload: PeticionCrearApuesta): Promise<RespuestaApuesta> {
  const respuesta = await clienteAPI.post<RespuestaApuesta>('/api/bitacora', payload);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo guardar la apuesta');
  }
  return respuesta.data;
}

export async function listarApuestas(params: Record<string, string | number | undefined>): Promise<RespuestaListaApuestas> {
  const respuesta = await clienteAPI.get<RespuestaListaApuestas>('/api/bitacora', { params });
  if (!respuesta.data.exito) {
    throw new Error('No se pudo obtener la bitácora');
  }
  return respuesta.data;
}

export async function obtenerResumenApuestas(): Promise<RespuestaResumenApuestas> {
  const respuesta = await clienteAPI.get<RespuestaResumenApuestas>('/api/bitacora/resumen');
  if (!respuesta.data.exito) {
    throw new Error('No se pudo obtener el resumen de apuestas');
  }
  return respuesta.data;
}

export async function actualizarResultadoApuesta(
  apuestaId: string,
  payload: PeticionActualizarResultado
): Promise<RespuestaApuesta> {
  const respuesta = await clienteAPI.patch<RespuestaApuesta>(`/api/bitacora/${apuestaId}/resultado`, payload);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo actualizar el resultado');
  }
  return respuesta.data;
}

export async function eliminarApuesta(apuestaId: string): Promise<void> {
  const respuesta = await clienteAPI.delete(`/api/bitacora/${apuestaId}`);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo eliminar la apuesta');
  }
}
